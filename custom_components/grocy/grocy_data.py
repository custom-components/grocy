"""Communication with Grocy API."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, List

from aiohttp import hdrs, web
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pygrocy import EntityType, Grocy
from pygrocy.data_models.battery import Battery

from .const import CONF_API_KEY, CONF_PORT, CONF_URL
from .helpers import MealPlanItemWrapper, extract_base_url_and_path

_LOGGER = logging.getLogger(__name__)


class GrocyData:  # pylint: disable=too-many-public-methods
    """Handles communication and gets the data."""

    def __init__(self, hass, api):
        """Initialize Grocy data."""
        self.hass: HomeAssistant = hass
        self._api: Grocy = api

    async def async_update_stock(self):
        """Update stock data."""
        return await self.hass.async_add_executor_job(self._api.stock)

    async def async_update_chores(self):
        """Update chores data."""

        def action():
            return self._api.chores(get_details=True)

        return await self.hass.async_add_executor_job(action)

    async def async_update_overdue_chores(self):
        """Update overdue chores data."""
        query_filter = [f"next_estimated_execution_time<{datetime.now()}"]

        def action():
            return self._api.chores(get_details=True, query_filters=query_filter)

        return await self.hass.async_add_executor_job(action)

    async def async_get_config(self):
        """Get the configuration from Grocy."""
        return await self.hass.async_add_executor_job(self._api.get_system_config)

    async def async_update_tasks(self):
        """Update tasks data."""
        return await self.hass.async_add_executor_job(self._api.tasks)

    async def async_update_overdue_tasks(self):
        """Update overdue tasks data."""
        and_query_filter = [
            f"due_date<{datetime.now().date()}",
            # It's not possible to pass an empty value to Grocy, so use a regex that matches non-empty values to exclude empty str due_date.
            r"due_date§.*\S.*",
        ]

        def action():
            return self._api.tasks(query_filters=and_query_filter)

        return await self.hass.async_add_executor_job(action)

    async def async_update_shopping_list(self):
        """Update shopping list data."""

        def action():
            return self._api.shopping_list(get_details=True)

        return await self.hass.async_add_executor_job(action)

    async def async_update_expiring_products(self):
        """Update expiring products data."""

        def action():
            return self._api.due_products(get_details=True)

        return await self.hass.async_add_executor_job(action)

    async def async_update_expired_products(self):
        """Update expired products data."""

        def action():
            return self._api.expired_products(get_details=True)

        return await self.hass.async_add_executor_job(action)

    async def async_update_overdue_products(self):
        """Update overdue products data."""

        def action():
            return self._api.overdue_products(get_details=True)

        return await self.hass.async_add_executor_job(action)

    async def async_update_missing_products(self):
        """Update missing products data."""

        def action():
            return self._api.missing_products(get_details=True)

        return await self.hass.async_add_executor_job(action)

    async def async_update_meal_plan(self):
        """Update meal plan data."""
        yesterday = datetime.now() - timedelta(1)
        query_filter = [
            f"day>{yesterday.date()}"
        ]  # The >= condition is broken before Grocy 3.3.1. So use > to maintain backward compatibility.

        def action():
            meal_plan = self._api.meal_plan(
                get_details=True, query_filters=query_filter
            )
            plan = [MealPlanItemWrapper(item) for item in meal_plan]
            return sorted(plan, key=lambda item: item.meal_plan.day)

        return await self.hass.async_add_executor_job(action)

    async def async_update_batteries(self) -> List[Battery]:
        """Update batteries."""

        def action():
            return self._api.batteries(get_details=True)

        return await self.hass.async_add_executor_job(action)

    async def async_update_overdue_batteries(self) -> List[Battery]:
        """Update overdue batteries."""
        query_filter = [f"next_estimated_charge_time<{datetime.now()}"]

        def action():
            return self._api.batteries(query_filters=query_filter, get_details=True)

        return await self.hass.async_add_executor_job(action)

    async def async_execute_chore(
        self, chore_id: str, done_by: str, skipped: str = False
    ) -> None:
        """Execute a chore."""

        def action():
            self._api.execute_chore(chore_id, done_by, skipped=skipped)

        return await self.hass.async_add_executor_job(action)

    async def async_complete_task(self, task_id: str) -> None:
        """Complete  a task."""

        def action():
            self._api.complete_task(task_id)

        return await self.hass.async_add_executor_job(action)

    async def async_add_product(self, product_id: str, amount: str, price: str) -> None:
        """Add a product."""

        def action():
            self._api.add_product(product_id, amount, price)

        return await self.hass.async_add_executor_job(action)

    async def async_consume_product(  # pylint: disable=too-many-arguments
        self,
        product_id: str,
        amount: str,
        spoiled: bool,
        transaction_type: str,
        allow_subproduct_substitution: bool = False,
    ) -> None:
        """Consume a product."""

        def action():
            self._api.consume_product(
                product_id,
                amount,
                spoiled=spoiled,
                transaction_type=transaction_type,
                allow_subproduct_substitution=allow_subproduct_substitution,
            )

        return await self.hass.async_add_executor_job(action)

    async def async_open_product(
        self,
        product_id: str,
        amount: str,
        allow_subproduct_substitution: bool = False,
    ) -> None:
        """Open a product."""

        def action():
            self._api.open_product(
                product_id,
                amount,
                allow_subproduct_substitution,
            )

        return await self.hass.async_add_executor_job(action)

    async def async_consume_recipe(self, recipe_id: str) -> None:
        """Consume a recipe."""

        def action():
            self._api.consume_recipe(recipe_id)

        return await self.hass.async_add_executor_job(action)

    async def async_track_battery(self, battery_id: str) -> None:
        """Track a battery."""

        def action():
            self._api.charge_battery(battery_id)

        return await self.hass.async_add_executor_job(action)

    async def async_add_generic(self, entity_type: EntityType, data: Any) -> None:
        """Add generic object."""

        def action():
            self._api.add_generic(entity_type, data)

        return await self.hass.async_add_executor_job(action)


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
