""" Representation of a Grocy instance """
import asyncio
import hashlib

from datetime import timedelta
from pygrocy import Grocy, TransactionType

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import CONF_API_KEY, CONF_PORT, CONF_URL, CONF_VERIFY_SSL
from homeassistant.util import Throttle

from .helpers import MealPlanItem
from .const import (
    CONF_ALLOW_CHORES,
    CONF_ALLOW_MEAL_PLAN,
    CONF_ALLOW_PRODUCTS,
    CONF_ALLOW_SHOPPING_LIST,
    CONF_ALLOW_STOCK,
    CONF_ALLOW_TASKS,
    CONF_MASTER_INSTANCE,
    DEFAULT_CONF_ALLOW_CHORES,
    DEFAULT_CONF_ALLOW_MEAL_PLAN,
    DEFAULT_CONF_ALLOW_PRODUCTS,
    DEFAULT_CONF_ALLOW_SHOPPING_LIST,
    DEFAULT_CONF_ALLOW_STOCK,
    DEFAULT_CONF_ALLOW_TASKS,
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
    LOGGER,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)


class GrocyInstance:
    """ Manages a single Grocy instance """

    def __init__(self, hass, config_entry) -> None:
        """Initialize the system."""
        self.hass = hass
        self.config_entry = config_entry

        self.available = True
        self.api = None

        self._current_option_allow_chores = self.option_allow_chores
        self._current_option_allow_meal_plan = self.option_allow_meal_plan
        self._current_option_allow_products = self.option_allow_products
        self._current_option_allow_shopping_list = self.option_allow_shopping_list
        self._current_option_allow_stock = self.option_allow_stock
        self._current_option_allow_tasks = self.option_allow_tasks

    @property
    def client(self) -> str:
        """Return the unique identifier of the instance."""
        return self.config_entry.unique_id

    @property
    def instanceid(self) -> str:
        """Return the unique identifier of the instance."""
        return self.config_entry.unique_id

    @property
    def master(self) -> bool:
        """Instance which is used with Grocy without defining id."""
        return self.config_entry.options[CONF_MASTER_INSTANCE]

    @property
    def option_allow_chores(self) -> bool:
        """Allow loading chores sensor from instance."""
        return self.config_entry.options.get(
            CONF_ALLOW_CHORES, DEFAULT_CONF_ALLOW_CHORES
        )

    @property
    def option_allow_meal_plan(self) -> bool:
        """Allow loading meal plan sensor from instance."""
        return self.config_entry.options.get(
            CONF_ALLOW_MEAL_PLAN, DEFAULT_CONF_ALLOW_MEAL_PLAN
        )

    @property
    def option_allow_products(self) -> bool:
        """Allow loading products sensor from instance."""
        return self.config_entry.options.get(
            CONF_ALLOW_PRODUCTS, DEFAULT_CONF_ALLOW_PRODUCTS
        )

    @property
    def option_allow_shopping_list(self) -> bool:
        """Allow loading shopping list sensor from instance."""
        return self.config_entry.options.get(
            CONF_ALLOW_SHOPPING_LIST, DEFAULT_CONF_ALLOW_SHOPPING_LIST
        )

    @property
    def option_allow_stock(self) -> bool:
        """Allow loading stock sensors from instance."""
        return self.config_entry.options.get(CONF_ALLOW_STOCK, DEFAULT_CONF_ALLOW_STOCK)

    @property
    def option_allow_tasks(self) -> bool:
        """Allow loading tasks sensor from instance."""
        return self.config_entry.options.get(CONF_ALLOW_TASKS, DEFAULT_CONF_ALLOW_TASKS)

    async def async_setup(self) -> bool:
        """Set up a Grocy instance."""
        LOGGER.debug("Setting up")
        try:
            self.api = await get_instance(
                self.hass,
                self.config_entry.data,
                # self.async_add_device_callback,
                # self.async_connection_status_callback,
            )

        # except CannotConnect:
        #     raise ConfigEntryNotReady

        except Exception as err:  # pylint: disable=broad-except
            LOGGER.error("Error connecting with deCONZ gateway: %s", err)
            return False

        # for component in SUPPORTED_PLATFORMS:
        #     self.hass.async_create_task(
        #         self.hass.config_entries.async_forward_entry_setup(
        #             self.config_entry, component
        #         )
        #     )

        # self.api.start()

        # self.config_entry.add_update_listener(self.async_config_entry_updated)

        return True


async def get_instance(hass, config) -> Grocy:
    """Create a gateway object and verify configuration."""
    # session = aiohttp_client.async_get_clientsession(hass)

    url = config.get(CONF_URL)
    api_key = config.get(CONF_API_KEY)
    verify_ssl = config.get(CONF_VERIFY_SSL)
    port_number = config.get(CONF_PORT)
    hash_key = hashlib.md5(api_key.encode("utf-8") + url.encode("utf-8")).hexdigest()

    grocy = Grocy(url, api_key, port_number, verify_ssl)
    hass.data[DOMAIN]["client"] = GrocyData(hass, grocy)
    hass.data[DOMAIN]["hash_key"] = hash_key
    hass.data[DOMAIN]["url"] = f"{url}:{port_number}"

    return grocy
    # try:
    #     with async_timeout.timeout(10):
    #         await deconz.initialize()
    #     return deconz

    # except errors.Unauthorized:
    #     LOGGER.warning("Invalid key for deCONZ at %s", config[CONF_HOST])
    #     raise AuthenticationRequired

    # except (asyncio.TimeoutError, errors.RequestError):
    #     LOGGER.error("Error connecting to deCONZ gateway at %s", config[CONF_HOST])
    #     raise CannotConnect


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

