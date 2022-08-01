"""Communication with Grocy API."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List

from aiohttp import hdrs, web
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pygrocy.data_models.battery import Battery

from .const import (
    ATTR_BATTERIES,
    ATTR_CHORES,
    ATTR_EXPIRED_PRODUCTS,
    ATTR_EXPIRING_PRODUCTS,
    ATTR_MEAL_PLAN,
    ATTR_MISSING_PRODUCTS,
    ATTR_OVERDUE_BATTERIES,
    ATTR_OVERDUE_CHORES,
    ATTR_OVERDUE_PRODUCTS,
    ATTR_OVERDUE_TASKS,
    ATTR_SHOPPING_LIST,
    ATTR_STOCK,
    ATTR_TASKS,
    CONF_API_KEY,
    CONF_PORT,
    CONF_URL,
)
from .helpers import MealPlanItemWrapper, extract_base_url_and_path

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
            ATTR_OVERDUE_PRODUCTS: self.async_update_overdue_products,
            ATTR_MISSING_PRODUCTS: self.async_update_missing_products,
            ATTR_MEAL_PLAN: self.async_update_meal_plan,
            ATTR_OVERDUE_CHORES: self.async_update_overdue_chores,
            ATTR_OVERDUE_TASKS: self.async_update_overdue_tasks,
            ATTR_BATTERIES: self.async_update_batteries,
            ATTR_OVERDUE_BATTERIES: self.async_update_overdue_batteries,
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

        query_filter = [f"next_estimated_execution_time<{datetime.now()}"]

        def wrapper():
            return self.api.chores(get_details=True, query_filters=query_filter)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_get_config(self):
        """Get the configuration from Grocy."""

        def wrapper():
            return self.api.get_system_config()

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_tasks(self):
        """Update tasks data."""

        return await self.hass.async_add_executor_job(self.api.tasks)

    async def async_update_overdue_tasks(self):
        """Update overdue tasks data."""

        and_query_filter = [
            f"due_date<{datetime.now().date()}",
            # It's not possible to pass an empty value to Grocy, so use a regex that matches non-empty values to exclude empty str due_date.
            r"due_date§.*\S.*",
        ]

        def wrapper():
            return self.api.tasks(query_filters=and_query_filter)

        return await self.hass.async_add_executor_job(wrapper)

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

    async def async_update_overdue_products(self):
        """Update overdue products data."""

        def wrapper():
            return self.api.overdue_products(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_missing_products(self):
        """Update missing products data."""

        def wrapper():
            return self.api.missing_products(True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_meal_plan(self):
        """Update meal plan data."""

        # The >= condition is broken before Grocy 3.3.1. So use > to maintain backward compatibility.
        yesterday = datetime.now() - timedelta(1)
        query_filter = [f"day>{yesterday.date()}"]

        def wrapper():
            meal_plan = self.api.meal_plan(get_details=True, query_filters=query_filter)
            plan = [MealPlanItemWrapper(item) for item in meal_plan]
            return sorted(plan, key=lambda item: item.meal_plan.day)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_batteries(self) -> List[Battery]:
        """Update batteries."""

        def wrapper():
            return self.api.batteries(get_details=True)

        return await self.hass.async_add_executor_job(wrapper)

    async def async_update_overdue_batteries(self) -> List[Battery]:
        """Update overdue batteries."""

        def wrapper():
            filter_query = [f"next_estimated_charge_time<{datetime.now()}"]
            return self.api.batteries(filter_query, get_details=True)

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
