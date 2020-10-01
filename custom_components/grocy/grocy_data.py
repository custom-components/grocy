from aiohttp import hdrs, web
from datetime import timedelta, datetime
import logging
import pytz

from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    CONF_URL,
    CONF_PORT,
    GrocyEntityType,
)
from .helpers import MealPlanItem

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)
_LOGGER = logging.getLogger(__name__)

utc = pytz.UTC


class GrocyData:
    """This class handle communication and stores the data."""

    def __init__(self, hass, client):
        """Initialize the class."""
        self.hass = hass
        self.client = client
        self.sensor_types_dict = {
            GrocyEntityType.STOCK: self.async_update_stock,
            GrocyEntityType.CHORES: self.async_update_chores,
            GrocyEntityType.TASKS: self.async_update_tasks,
            GrocyEntityType.SHOPPING_LIST: self.async_update_shopping_list,
            GrocyEntityType.EXPIRING_PRODUCTS: self.async_update_expiring_products,
            GrocyEntityType.EXPIRED_PRODUCTS: self.async_update_expired_products,
            GrocyEntityType.MISSING_PRODUCTS: self.async_update_missing_products,
            GrocyEntityType.MEAL_PLAN: self.async_update_meal_plan,
            GrocyEntityType.OVERDUE_CHORES: self.async_update_overdue_chores,
            GrocyEntityType.OVERDUE_TASKS: self.async_update_overdue_tasks,
        }
        self.sensor_update_dict = {
            GrocyEntityType.STOCK: None,
            GrocyEntityType.CHORES: None,
            GrocyEntityType.TASKS: None,
            GrocyEntityType.SHOPPING_LIST: None,
            GrocyEntityType.EXPIRING_PRODUCTS: None,
            GrocyEntityType.EXPIRED_PRODUCTS: None,
            GrocyEntityType.MISSING_PRODUCTS: None,
            GrocyEntityType.MEAL_PLAN: None,
            GrocyEntityType.OVERDUE_CHORES: None,
            GrocyEntityType.OVERDUE_TASKS: None,
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
                return await self.sensor_types_dict[sensor_type]()

    async def async_update_stock(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        return await self.hass.async_add_executor_job(self.client.stock)

    async def async_update_chores(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.chores(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_overdue_chores(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.chores(True)

        chores = await self.hass.async_add_executor_job(wrapper)
        overdue_chores = []
        for chore in chores:
            if chore.next_estimated_execution_time:
                now = datetime.now().replace(tzinfo=utc)
                due = chore.next_estimated_execution_time.replace(tzinfo=utc)
                if due < now:
                    overdue_chores.append(chore)
        return overdue_chores

    async def async_get_config(self):
        """Get the configuration from Grocy."""

        def wrapper():
            return self.client._api_client._do_get_request("/api/system/config")

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_tasks(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        return await self.hass.async_add_executor_job(self.client.tasks)

    async def async_update_overdue_tasks(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        tasks = await self.hass.async_add_executor_job(self.client.tasks)

        overdue_tasks = []
        for task in tasks:
            if task.due_date:
                now = datetime.now().replace(tzinfo=utc)
                due = task.due_date.replace(tzinfo=utc)
                if due < now:
                    overdue_tasks.append(task)
        return overdue_tasks

    async def async_update_shopping_list(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.shopping_list(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_expiring_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.expiring_products(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_expired_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.expired_products(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_missing_products(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            return self.client.missing_products(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_meal_plan(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        def wrapper():
            meal_plan = self.client.meal_plan(True)
            today = datetime.today().date()
            plan = [
                MealPlanItem(item) for item in meal_plan if item.day.date() >= today
            ]
            return sorted(plan, key=lambda item: item.day)

        return await self.hass.async_add_executor_job(wrapper)


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
