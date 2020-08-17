"""
The integration for grocy.
"""
import asyncio
import hashlib
import os
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_PORT, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.helpers import discovery, entity_component
from homeassistant.util import Throttle
from integrationhelper.const import CC_STARTUP_VERSION
from pygrocy import Grocy, TransactionType
from datetime import datetime
import iso8601

from .const import (
    LOGGER,
    CHORES_NAME,
    TASKS_NAME,
    CONF_ENABLED,
    CONF_NAME,
    DEFAULT_CONF_NAME,
    DEFAULT_PORT_NUMBER,
    DOMAIN,
    EXPIRED_PRODUCTS_NAME,
    EXPIRING_PRODUCTS_NAME,
    ISSUE_URL,
    MISSING_PRODUCTS_NAME,
    MEAL_PLAN_NAME,
    PLATFORMS,
    REQUIRED_FILES,
    SHOPPING_LIST_NAME,
    STARTUP,
    STOCK_NAME,
    VERSION,
)

from .helpers import MealPlanItem
from .services import async_setup_services

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)


async def async_setup(hass, config):
    """Old setup way."""
    return True


async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""

    conf = hass.data.get(DOMAIN)
    if config_entry.source == config_entries.SOURCE_IMPORT:
        if conf is None:
            hass.async_create_task(
                hass.config_entries.async_remove(config_entry.entry_id)
            )
        return False

    # Print startup message
    LOGGER.info(
        CC_STARTUP_VERSION.format(name=DOMAIN, version=VERSION, issue_link=ISSUE_URL)
    )

    # Check that all required files are present
    if not await hass.async_add_executor_job(check_files, hass):
        return False

    # Create DATA dict
    hass.data[DOMAIN] = {}

    # Get "global" configuration.
    url = config_entry.data.get(CONF_URL)
    api_key = config_entry.data.get(CONF_API_KEY)
    verify_ssl = config_entry.data.get(CONF_VERIFY_SSL)
    port_number = config_entry.data.get(CONF_PORT)
    hash_key = hashlib.md5(api_key.encode("utf-8") + url.encode("utf-8")).hexdigest()

    # Configure the client.
    grocy = Grocy(url, api_key, port_number, verify_ssl)
    hass.data[DOMAIN]["instance"] = grocy
    hass.data[DOMAIN]["client"] = GrocyData(hass, grocy)
    hass.data[DOMAIN]["hash_key"] = hash_key
    hass.data[DOMAIN]["url"] = f"{url}:{port_number}"

    # Add sensors
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )
    # Add binary sensors
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )

    # Setup services
    await async_setup_services(hass)

    return True


class GrocyData:
    """This class handle communication and stores the data."""

    def __init__(self, hass, client):
        """Initialize the class."""
        self.hass = hass
        self.client = client
        self.sensor_types_dict = {
            STOCK_NAME: self.async_update_stock,
            CHORES_NAME: self.async_update_chores,
            TASKS_NAME: self.async_update_tasks,
            SHOPPING_LIST_NAME: self.async_update_shopping_list,
            EXPIRING_PRODUCTS_NAME: self.async_update_expiring_products,
            EXPIRED_PRODUCTS_NAME: self.async_update_expired_products,
            MISSING_PRODUCTS_NAME: self.async_update_missing_products,
            MEAL_PLAN_NAME: self.async_update_meal_plan,
        }
        self.sensor_update_dict = {
            STOCK_NAME: None,
            CHORES_NAME: None,
            TASKS_NAME: None,
            SHOPPING_LIST_NAME: None,
            EXPIRING_PRODUCTS_NAME: None,
            EXPIRED_PRODUCTS_NAME: None,
            MISSING_PRODUCTS_NAME: None,
            MEAL_PLAN_NAME: None,
        }

    async def async_update_data(self, sensor_type):
        """Update data."""
        sensor_update = self.sensor_update_dict[sensor_type]
        db_changed = await self.hass.async_add_executor_job(
            self.client.get_last_db_changed
        )
        if db_changed != sensor_update:
            self.sensor_update_dict[sensor_type] = db_changed
            if sensor_type in self.sensor_types_dict:
                # This is where the main logic to update platform data goes.
                self.hass.async_create_task(self.sensor_types_dict[sensor_type]())

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_stock(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        self.hass.data[DOMAIN][STOCK_NAME] = await self.hass.async_add_executor_job(
            self.client.stock
        )

    async def async_update_chores(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.chores(True)

        self.hass.data[DOMAIN][CHORES_NAME] = await self.hass.async_add_executor_job(
            wrapper
        )

    async def async_update_tasks(self):
        """Update data."""
        # This is where the main logic to update platform data goes.

        self.hass.data[DOMAIN][TASKS_NAME] = await self.hass.async_add_executor_job(
            self.client.tasks
        )

    async def async_update_shopping_list(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.shopping_list(True)

        self.hass.data[DOMAIN][
            SHOPPING_LIST_NAME
        ] = await self.hass.async_add_executor_job(wrapper)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_expiring_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.expiring_products(True)

        self.hass.data[DOMAIN][
            EXPIRING_PRODUCTS_NAME
        ] = await self.hass.async_add_executor_job(wrapper)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_expired_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.expired_products(True)

        self.hass.data[DOMAIN][
            EXPIRED_PRODUCTS_NAME
        ] = await self.hass.async_add_executor_job(wrapper)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_missing_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.missing_products(True)

        self.hass.data[DOMAIN][
            MISSING_PRODUCTS_NAME
        ] = await self.hass.async_add_executor_job(wrapper)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update_meal_plan(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            meal_plan = self.client.meal_plan(True)
            base_url = self.hass.data[DOMAIN]["url"]
            return [MealPlanItem(item, base_url) for item in meal_plan]

        self.hass.data[DOMAIN][MEAL_PLAN_NAME] = await self.hass.async_add_executor_job(
            wrapper
        )


def check_files(hass):
    """Return bool that indicates if all files are present."""
    # Verify that the user downloaded all files.
    base = "{}/custom_components/{}/".format(hass.config.path(), DOMAIN)
    missing = []
    for file in REQUIRED_FILES:
        fullpath = "{}{}".format(base, file)
        if not os.path.exists(fullpath):
            missing.append(file)

    if missing:
        LOGGER.critical("The following files are missing: %s", str(missing))
        returnvalue = False
    else:
        returnvalue = True

    return returnvalue


async def async_remove_entry(hass, config_entry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        LOGGER.info("Successfully removed sensor from the grocy integration")
    except ValueError as error:
        LOGGER.exception(error)
        pass
    try:
        await hass.config_entries.async_forward_entry_unload(
            config_entry, "binary_sensor"
        )
        LOGGER.info("Successfully removed sensor from the grocy integration")
    except ValueError as error:
        LOGGER.exception(error)
        pass
