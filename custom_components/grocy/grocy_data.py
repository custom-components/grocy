"""Communication with Grocy API."""
import logging
from datetime import datetime

from aiohttp import hdrs, web
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ATTR_CHORES,
    ATTR_EXPIRED_PRODUCTS,
    ATTR_EXPIRING_PRODUCTS,
    ATTR_MEAL_PLAN,
    ATTR_MISSING_PRODUCTS,
    ATTR_OVERDUE_CHORES,
    ATTR_OVERDUE_TASKS,
    ATTR_SHOPPING_LIST,
    ATTR_STOCK,
    ATTR_TASKS,
    CONF_API_KEY,
    CONF_PORT,
    CONF_URL,
)
from .helpers import MealPlanItem, extract_base_url_and_path

_LOGGER = logging.getLogger(__name__)


class GrocyData:
    """Handles communication and gets the data."""

    def __init__(self, hass, api):
        """Initialize Grocy data."""
        self.hass = hass
        self.api = api
        self.entity_update_method = {
            ATTR_STOCK: self.async_update_stock,
            ATTR_CHORES: self.async_update_chores,
            ATTR_TASKS: self.async_update_tasks,
            ATTR_SHOPPING_LIST: self.async_update_shopping_list,
            ATTR_EXPIRING_PRODUCTS: self.async_update_expiring_products,
            ATTR_EXPIRED_PRODUCTS: self.async_update_expired_products,
            ATTR_MISSING_PRODUCTS: self.async_update_missing_products,
            ATTR_MEAL_PLAN: self.async_update_meal_plan,
            ATTR_OVERDUE_CHORES: self.async_update_overdue_chores,
            ATTR_OVERDUE_TASKS: self.async_update_overdue_tasks,
        }

    async def async_update_data(self, entity_key):
        """Update data."""
        if entity_key in self.entity_update_method:
            return await self.entity_update_method[entity_key]()

    async def async_update_stock(self):
        """Update stock data."""
        return await self.hass.async_add_executor_job(self.api.stock)

    async def async_update_chores(self):
        """Update chores data."""

        def wrapper():
            return self.api.chores(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_overdue_chores(self):
        """Update overdue chores data."""

        def wrapper():
            return self.api.chores(True)

        chores = await self.hass.async_add_executor_job(wrapper)
        overdue_chores = []
        for chore in chores:
            if chore.next_estimated_execution_time:
                now = datetime.now()
                due = chore.next_estimated_execution_time
                if due < now:
                    overdue_chores.append(chore)
        return overdue_chores

    async def async_get_config(self):
        """Get the configuration from Grocy."""

        def wrapper():
            return self.api._api_client._do_get_request(
                "system/config"
            )  # TODO Make endpoint available in pygrocy

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_tasks(self):
        """Update tasks data."""
        return await self.hass.async_add_executor_job(self.api.tasks)

    async def async_update_overdue_tasks(self):
        """Update overdue tasks data."""
        tasks = await self.hass.async_add_executor_job(self.api.tasks)

        overdue_tasks = []
        for task in tasks:
            if task.due_date:
                current_date = datetime.now().date()
                due_date = task.due_date
                if due_date < current_date:
                    overdue_tasks.append(task)
        return overdue_tasks

    async def async_update_shopping_list(self):
        """Update shopping list data."""

        def wrapper():
            return self.api.shopping_list(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_expiring_products(self):
        """Update expiring products data."""

        def wrapper():
            return self.api.due_products(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_expired_products(self):
        """Update expired products data."""

        def wrapper():
            return self.api.expired_products(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_missing_products(self):
        """Update missing products data."""

        def wrapper():
            return self.api.missing_products(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_meal_plan(self):
        """Update meal plan data."""

        def wrapper():
            meal_plan = self.api.meal_plan(True)
            today = datetime.today().date()
            plan = [MealPlanItem(item) for item in meal_plan if item.day >= today]
            return sorted(plan, key=lambda item: item.day)

        return await self.hass.async_add_executor_job(wrapper)


async def async_setup_endpoint_for_image_proxy(
    hass: HomeAssistant, config_entry: ConfigEntry
):
    """Setup and register the image api for grocy images with HA."""
    session = async_get_clientsession(hass)

    url = config_entry.get(CONF_URL)
    (grocy_base_url, grocy_path) = extract_base_url_and_path(url)
    api_key = config_entry.get(CONF_API_KEY)
    port_number = config_entry.get(CONF_PORT)
    if grocy_path:
        grocy_full_url = f"{grocy_base_url}:{port_number}/{grocy_path}"
    else:
        grocy_full_url = f"{grocy_base_url}:{port_number}"

    _LOGGER.debug("Generated image api url to grocy: '%s'", grocy_full_url)
    hass.http.register_view(GrocyPictureView(session, grocy_full_url, api_key))


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
        """GET request for the image."""
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
