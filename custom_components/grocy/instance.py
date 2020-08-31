""" Representation of a Grocy instance """
import asyncio
import hashlib
import aiohttp

from aiohttp import hdrs, web
from datetime import timedelta, datetime
from pygrocy import Grocy, TransactionType

from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import CONF_API_KEY, CONF_PORT, CONF_URL, CONF_VERIFY_SSL
from homeassistant.util import Throttle
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .helpers import MealPlanItem
from .const import (
    CONF_ALLOW_CHORES,
    CONF_ALLOW_MEAL_PLAN,
    CONF_ALLOW_SHOPPING_LIST,
    CONF_ALLOW_STOCK,
    CONF_ALLOW_TASKS,
    DEFAULT_CONF_ALLOW_CHORES,
    DEFAULT_CONF_ALLOW_MEAL_PLAN,
    DEFAULT_CONF_ALLOW_SHOPPING_LIST,
    DEFAULT_CONF_ALLOW_STOCK,
    DEFAULT_CONF_ALLOW_TASKS,
    CHORES_NAME,
    TASKS_NAME,
    DEFAULT_PORT_NUMBER,
    DOMAIN,
    EXPIRED_PRODUCTS_NAME,
    EXPIRING_PRODUCTS_NAME,
    MISSING_PRODUCTS_NAME,
    MEAL_PLAN_NAME,
    REQUIRED_FILES,
    SHOPPING_LIST_NAME,
    STARTUP,
    STOCK_NAME,
    VERSION,
    LOGGER,
    SUPPORTED_PLATFORMS,
    NEW_BINARY_SENSOR,
    NEW_SENSOR,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

class GrocyPictureView(HomeAssistantView):
    """View to render pictures from grocy without auth."""

    requires_auth = False
    url = '/api/grocy/{picture_type}/{filename}'
    name = "api:grocy:picture"

    def __init__(self, session, base_url, api_key):
        self._session = session
        self._base_url = base_url
        self._api_key = api_key

    async def get(self, request, picture_type: str, filename: str) -> web.Response:
        width = request.query.get('width', 400)
        url = f"{self._base_url}/api/files/{picture_type}/{filename}"
        url = f"{url}?force_serve_as=picture&best_fit_width={int(width)}"
        headers = {'GROCY-API-KEY': self._api_key, 'accept': '*/*'}

        async with self._session.get(url, headers=headers) as resp:
            resp.raise_for_status()

            response_headers = {}
            for name, value in resp.headers.items():
                if name in (
                    hdrs.CACHE_CONTROL,
                    hdrs.CONTENT_DISPOSITION,
                    hdrs.CONTENT_LENGTH,
                    hdrs.CONTENT_TYPE,
                    hdrs.CONTENT_ENCODING,
                ):
                    response_headers[name] = value

            body = await resp.read()
            return web.Response(body=body, headers=response_headers)

class GrocyInstance:
    """ Manages a single Grocy instance """

    def __init__(self, hass, config_entry) -> None:
        """Initialize the system."""
        self.hass = hass
        self.config_entry = config_entry

        self.available = True
        self.api = None
        self.listeners = []

        self._current_option_allow_chores = self.option_allow_chores
        self._current_option_allow_meal_plan = self.option_allow_meal_plan
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
            self.api = await get_instance(self.hass, self.config_entry.data)

        except Exception as err:  # pylint: disable=broad-except
            LOGGER.error("Error connecting with Grocy instance: %s", err)
            return False

        for component in SUPPORTED_PLATFORMS:
            self.hass.async_create_task(
                self.hass.config_entries.async_forward_entry_setup(
                    self.config_entry, component
                )
            )

        self.config_entry.add_update_listener(self.async_config_entry_updated)

        return True

    @staticmethod
    async def async_config_entry_updated(hass, entry) -> None:
        """Handle signals of config entry being updated."""
        instance = hass.data[DOMAIN]["instance"]

        if not instance:
            return

        return await instance.options_updated()

    async def options_updated(self):
        """Manage entities affected by config entry options."""

        hash_key = self.hass.data[DOMAIN].get("hash_key")

        if self._current_option_allow_chores != self.option_allow_chores:
            self._current_option_allow_chores = self.option_allow_chores
            if self._current_option_allow_chores:
                self.async_add_entity_callback(NEW_SENSOR, CHORES_NAME)
            else:
                # remove sensor
                self.async_remove_entity_callback(
                    NEW_SENSOR, "{}-{}".format(hash_key, CHORES_NAME)
                )

        if self._current_option_allow_meal_plan != self.option_allow_meal_plan:
            self._current_option_allow_meal_plan = self.option_allow_meal_plan
            if self._current_option_allow_meal_plan:
                self.async_add_entity_callback(NEW_SENSOR, MEAL_PLAN_NAME)

        if self._current_option_allow_shopping_list != self.option_allow_shopping_list:
            self._current_option_allow_shopping_list = self.option_allow_shopping_list
            if self._current_option_allow_shopping_list:
                self.async_add_entity_callback(NEW_SENSOR, SHOPPING_LIST_NAME)

        if self._current_option_allow_stock != self.option_allow_stock:
            self._current_option_allow_stock = self.option_allow_stock
            if self._current_option_allow_stock:
                self.async_add_entity_callback(
                    NEW_SENSOR, [STOCK_NAME],
                )
                self.async_add_entity_callback(
                    NEW_BINARY_SENSOR,
                    [
                        EXPIRING_PRODUCTS_NAME,
                        EXPIRED_PRODUCTS_NAME,
                        MISSING_PRODUCTS_NAME,
                    ],
                )

        if self._current_option_allow_tasks != self.option_allow_tasks:
            self._current_option_allow_tasks = self.option_allow_tasks
            if self._current_option_allow_tasks:
                self.async_add_entity_callback(NEW_SENSOR, TASKS_NAME)

    @callback
    def async_remove_entity_callback(self, sensor_type, sensor) -> None:
        """Handle event of removing an entity."""
        LOGGER.debug("remove entity callback")
        LOGGER.debug(sensor)
        if not isinstance(sensor, list):
            sensor = [sensor]
        async_dispatcher_send(self.hass, self.async_signal_remove(sensor_type), sensor)

    @callback
    def async_signal_remove(self, sensor_type) -> str:
        """Event to signal removal."""
        LOGGER.debug("signal remove")

        return f"grocy-remove-{self.instanceid}"

    @callback
    def async_add_entity_callback(self, sensor_type, sensor) -> None:
        """Handle event of new entity creation."""
        LOGGER.debug("add entity callback")
        if not isinstance(sensor, list):
            sensor = [sensor]
        async_dispatcher_send(
            self.hass, self.async_signal_new_entity(sensor_type), sensor
        )

    @callback
    def async_signal_new_entity(self, sensor_type) -> str:
        """Event to signal new entity."""
        new_sensor = {
            NEW_SENSOR: f"grocy_new_sensor",
            NEW_BINARY_SENSOR: f"grocy_new_binary_sensor",
        }
        return new_sensor[sensor_type]


async def get_instance(hass, config) -> Grocy:
    """Create a gateway object and verify configuration."""
    LOGGER.debug("Getting Grocy instance.")
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
            today = datetime.today().date()
            date_format = '%Y-%m-%d %H:%M:%S.%f'
            plan = [MealPlanItem(item) for item in meal_plan if item.day.date() >= today]
            return sorted(plan, key=lambda item: item.day)

        self.hass.data[DOMAIN][MEAL_PLAN_NAME] = await self.hass.async_add_executor_job(
            wrapper
        )

async def async_setup_api(hass, config):
    session = async_get_clientsession(hass)

    url = config.get(CONF_URL)
    api_key = config.get(CONF_API_KEY)
    port_number = config.get(CONF_PORT)
    base_url = f"{url}:{port_number}"
    hass.http.register_view(GrocyPictureView(session, base_url, api_key))
