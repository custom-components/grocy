"""
The integration for grocy.
"""
import logging
import os
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_API_KEY,
    CONF_URL,
    CONF_VERIFY_SSL,
    CONF_PORT,
)
from homeassistant.helpers import discovery
from homeassistant.util import Throttle
from homeassistant.core import callback

from .const import (
    CONF_ENABLED,
    CONF_NAME,
    CONF_SENSOR,
    CONF_BINARY_SENSOR,
    DEFAULT_NAME,
    DOMAIN,
    DEFAULT_PORT_NUMBER,
    DOMAIN_DATA, ISSUE_URL,
    PLATFORMS,
    REQUIRED_FILES,
    STARTUP,
    VERSION,
)

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
    # Import client from a external python package hosted on PyPi
    from pygrocy import Grocy, TransactionType
    from datetime import datetime
    import iso8601

    # Print startup message
    startup = STARTUP.format(name=DOMAIN, version=VERSION, issueurl=ISSUE_URL)
    _LOGGER.info(startup)

    # Check that all required files are present
    file_check = await check_files(hass)
    if not file_check:
        return False

    # Create DATA dict
    hass.data[DOMAIN_DATA] = {}

    # Get "global" configuration.
    url = config[DOMAIN].get(CONF_URL)
    api_key = config[DOMAIN].get(CONF_API_KEY)
    verify_ssl = config[DOMAIN].get(CONF_VERIFY_SSL)
    port_number = config[DOMAIN].get(CONF_PORT)

    # Configure the client.
    grocy = Grocy(url, api_key, port_number, verify_ssl)
    hass.data[DOMAIN_DATA]["client"] = GrocyData(hass, grocy)

    # Load platforms
    for platform in PLATFORMS:
        # Get platform specific configuration
        platform_config = config[DOMAIN].get(platform, {})

        # If platform is not enabled, skip.
        if not platform_config:
            continue

        for entry in platform_config:
            entry_config = entry

            # If entry is not enabled, skip.
            if not entry_config[CONF_ENABLED]:
                continue

            hass.async_create_task(
                discovery.async_load_platform(
                    hass, platform, DOMAIN, entry_config, config
                )
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

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_stock(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN_DATA]["stock"] = (
            await self.hass.async_add_executor_job(self.client.stock, [True]))

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_chores(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN_DATA]["chores"] = (
            await self.hass.async_add_executor_job(self.client.chores, [True]))

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_expiring_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN_DATA]["expiring_products"] = (
            await self.hass.async_add_executor_job(
                self.client.expiring_products))


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
