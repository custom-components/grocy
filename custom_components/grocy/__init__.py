"""
The integration for grocy.
"""
import hashlib
import logging
import os
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (CONF_API_KEY, CONF_PORT, CONF_URL,
                                 CONF_VERIFY_SSL)
from homeassistant.core import callback
from homeassistant.helpers import discovery
from homeassistant.util import Throttle
from integrationhelper.const import CC_STARTUP_VERSION

from .const import (CHORES_NAME, CONF_BINARY_SENSOR, CONF_ENABLED, CONF_NAME,
                    CONF_SENSOR, DEFAULT_NAME, DEFAULT_PORT_NUMBER, DOMAIN,
                    DOMAIN_DATA, EXPIRED_PRODUCTS_NAME, EXPIRING_PRODUCTS_NAME,
                    ISSUE_URL, MISSING_PRODUCTS_NAME, PLATFORMS,
                    REQUIRED_FILES, SHOPPING_LIST_NAME, STARTUP, STOCK_NAME,
                    VERSION)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENABLED, default=True): cv.boolean,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

BINARY_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENABLED, default=True): cv.boolean,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_URL): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT_NUMBER): cv.port,
                vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean,
                vol.Optional(CONF_SENSOR): vol.All(
                    cv.ensure_list, [SENSOR_SCHEMA]
                ),
                vol.Optional(CONF_BINARY_SENSOR): vol.All(
                    cv.ensure_list, [BINARY_SENSOR_SCHEMA]
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up this component."""
    return True

async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""
    from pygrocy import Grocy, TransactionType
    from datetime import datetime
    import iso8601

    conf = hass.data.get(DOMAIN_DATA)
    if config_entry.source == config_entries.SOURCE_IMPORT:
        if conf is None:
            hass.async_create_task(
                hass.config_entries.async_remove(config_entry.entry_id)
            )
        return False

    # Print startup message
    _LOGGER.info(
        CC_STARTUP_VERSION.format(name=DOMAIN, version=VERSION, issue_link=ISSUE_URL)
    )

    # Check that all required files are present
    file_check = await check_files(hass)
    if not file_check:
        return False

    # Create DATA dict
    hass.data[DOMAIN_DATA] = {}

    # Get "global" configuration.
    url = config_entry.data.get(CONF_URL)
    api_key = config_entry.data.get(CONF_API_KEY)
    verify_ssl = config_entry.data.get(CONF_VERIFY_SSL)
    port_number = config_entry.data.get(CONF_PORT)
    hash_key = hashlib.md5(api_key.encode('utf-8') + url.encode('utf-8')).hexdigest()

    # Configure the client.
    grocy = Grocy(url, api_key, port_number, verify_ssl)
    hass.data[DOMAIN_DATA]["client"] = GrocyData(hass, grocy)
    hass.data[DOMAIN_DATA]["hash_key"] = hash_key

    # Add sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )
    # Add sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )

    @callback
    def handle_add_product(call):
        product_id = call.data['product_id']
        amount = call.data.get('amount', 0)
        price = call.data.get('price', None)
        grocy.add_product(product_id, amount, price)

    hass.services.async_register(DOMAIN, "add_product", handle_add_product)

    @callback
    def handle_consume_product(call):
        product_id = call.data['product_id']
        amount = call.data.get('amount', 0)
        spoiled = call.data.get('spoiled', False)

        transaction_type_raw = call.data.get('transaction_type', None)
        transaction_type = TransactionType.CONSUME

        if transaction_type_raw is not None:
            transaction_type = TransactionType[transaction_type_raw]
        grocy.consume_product(
            product_id, amount,
            spoiled=spoiled,
            transaction_type=transaction_type)

    hass.services.async_register(
        DOMAIN, "consume_product",
        handle_consume_product)

    @callback
    def handle_execute_chore(call):
        chore_id = call.data['chore_id']
        done_by = call.data.get('done_by', None)
        tracked_time_str = call.data.get('tracked_time', None)

        tracked_time = datetime.now()
        if tracked_time_str is not None:
            tracked_time = iso8601.parse_date(tracked_time_str)
        grocy.execute_chore(chore_id, done_by, tracked_time)

    hass.services.async_register(DOMAIN, "execute_chore", handle_execute_chore)

    return True

class GrocyData:
    """This class handle communication and stores the data."""

    def __init__(self, hass, client):
        """Initialize the class."""
        self.hass = hass
        self.client = client
        self.sensor_types_dict = { STOCK_NAME : self.async_update_stock,
            CHORES_NAME : self.async_update_chores,
            SHOPPING_LIST_NAME : self.async_update_shopping_list,
            EXPIRING_PRODUCTS_NAME : self.async_update_expiring_products,
            EXPIRED_PRODUCTS_NAME : self.async_update_expired_products,
            MISSING_PRODUCTS_NAME : self.async_update_missing_products,
        }
        self.sensor_update_dict = { STOCK_NAME : None,
            CHORES_NAME : None,
            SHOPPING_LIST_NAME : None,
            EXPIRING_PRODUCTS_NAME : None,
            EXPIRED_PRODUCTS_NAME : None,
            MISSING_PRODUCTS_NAME : None,
        }

    async def async_update_data(self, sensor_type):
        """Update data."""
        sensor_update = self.sensor_update_dict[sensor_type]        
        db_changed = await self.hass.async_add_executor_job(self.client.get_last_db_changed)
        if db_changed != sensor_update:
            self.sensor_update_dict[sensor_type] = db_changed
            if sensor_type in self.sensor_types_dict:
                # This is where the main logic to update platform data goes.
                self.hass.async_create_task(self.sensor_types_dict[sensor_type]())

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_stock(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN_DATA][STOCK_NAME] = (
            await self.hass.async_add_executor_job(self.client.stock, [True]))

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_chores(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN_DATA][CHORES_NAME] = (
            await self.hass.async_add_executor_job(self.client.chores, [True]))

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_shopping_list(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN_DATA][SHOPPING_LIST_NAME] = (
            await self.hass.async_add_executor_job(self.client.shopping_list, [True]))

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_expiring_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN_DATA][EXPIRING_PRODUCTS_NAME] = (
            await self.hass.async_add_executor_job(
                self.client.expiring_products, [True]))

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_expired_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN_DATA][EXPIRED_PRODUCTS_NAME] = (
            await self.hass.async_add_executor_job(
                self.client.expired_products, [True]))

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_missing_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN_DATA][MISSING_PRODUCTS_NAME] = (
            await self.hass.async_add_executor_job(
                self.client.missing_products, [True]))


async def check_files(hass):
    """Return bool that indicates if all files are present."""
    # Verify that the user downloaded all files.
    base = "{}/custom_components/{}/".format(hass.config.path(), DOMAIN)
    missing = []
    for file in REQUIRED_FILES:
        fullpath = "{}{}".format(base, file)
        if not os.path.exists(fullpath):
            missing.append(file)

    if missing:
        _LOGGER.critical("The following files are missing: %s", str(missing))
        returnvalue = False
    else:
        returnvalue = True

    return returnvalue

async def async_remove_entry(hass, config_entry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the grocy integration")
    except ValueError as error:
        _LOGGER.exception(error)
        pass
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "binary_sensor")
        _LOGGER.info("Successfully removed sensor from the grocy integration")
    except ValueError as error:
        _LOGGER.exception(error)
        pass
