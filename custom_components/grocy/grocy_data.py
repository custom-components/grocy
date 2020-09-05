from aiohttp import hdrs, web
from datetime import timedelta, datetime

from homeassistant.util import Throttle
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ALLOW_CHORES,
    CONF_ALLOW_MEAL_PLAN,
    CONF_ALLOW_SHOPPING_LIST,
    CONF_ALLOW_STOCK,
    CONF_ALLOW_TASKS,
    CONF_API_KEY,
    CONF_URL,
    CONF_PORT,
    DEFAULT_CONF_ALLOW_CHORES,
    DEFAULT_CONF_ALLOW_MEAL_PLAN,
    DEFAULT_CONF_ALLOW_SHOPPING_LIST,
    DEFAULT_CONF_ALLOW_STOCK,
    DEFAULT_CONF_ALLOW_TASKS,
    CHORES_NAME,
    TASKS_NAME,
    DOMAIN,
    EXPIRED_PRODUCTS_NAME,
    EXPIRING_PRODUCTS_NAME,
    MISSING_PRODUCTS_NAME,
    MEAL_PLAN_NAME,
    SHOPPING_LIST_NAME,
    STOCK_NAME,
)
from .helpers import MealPlanItem

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)


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
            date_format = "%Y-%m-%d %H:%M:%S.%f"
            plan = [
                MealPlanItem(item) for item in meal_plan if item.day.date() >= today
            ]
            return sorted(plan, key=lambda item: item.day)

        self.hass.data[DOMAIN][MEAL_PLAN_NAME] = await self.hass.async_add_executor_job(
            wrapper
        )


async def async_setup_image_api(hass, config):
    session = async_get_clientsession(hass)

    url = config.get(CONF_URL)
    api_key = config.get(CONF_API_KEY)
    port_number = config.get(CONF_PORT)
    base_url = f"{url}:{port_number}"
    hass.http.register_view(GrocyPictureView(session, base_url, api_key))


class GrocyPictureView(HomeAssistantView):
    """View to render pictures from grocy without auth."""

    requires_auth = False
    url = "/api/grocy/{picture_type}/{filename}"
    name = "api:grocy:picture"

    def __init__(self, session, base_url, api_key):
        self._session = session
        self._base_url = base_url
        self._api_key = api_key

    async def get(self, request, picture_type: str, filename: str) -> web.Response:
        width = request.query.get("width", 400)
        url = f"{self._base_url}/api/files/{picture_type}/{filename}"
        url = f"{url}?force_serve_as=picture&best_fit_width={int(width)}"
        headers = {"GROCY-API-KEY": self._api_key, "accept": "*/*"}

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
