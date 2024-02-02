"""Data update coordinator for Grocy."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from pygrocy import Grocy
from pygrocy.data_models.battery import Battery
from pygrocy.data_models.chore import Chore
from pygrocy.data_models.meal_items import MealPlanItem
from pygrocy.data_models.product import Product, ShoppingListProduct
from pygrocy.data_models.task import Task

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_API_KEY,
    CONF_PORT,
    CONF_URL,
    CONF_VERIFY_SSL,
    DOMAIN,
    SCAN_INTERVAL,
)
from .grocy_data import GrocyData
from .helpers import MealPlanItemWrapper, extract_base_url_and_path

_LOGGER = logging.getLogger(__name__)


@dataclass
class GrocyCoordinatorData:
    batteries: list[Battery] | None = None
    chores: list[Chore] | None = None
    expired_products: list[Product] | None = None
    expiring_products: list[Product] | None = None
    meal_plan: list[MealPlanItemWrapper] | None = None
    missing_products: list[Product] | None = None
    overdue_batteries: list[Battery] | None = None
    overdue_chores: list[Chore] | None = None
    overdue_products: list[Product] | None = None
    overdue_tasks: list[Task] | None = None
    shopping_list: list[ShoppingListProduct] | None = None
    stock: list[Product] | None = None
    tasks: list[Task] | None = None

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key: str):
        return getattr(self, key)


class GrocyDataUpdateCoordinator(DataUpdateCoordinator[GrocyCoordinatorData]):
    """Grocy data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize Grocy data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

        url = self.config_entry.data[CONF_URL]
        api_key = self.config_entry.data[CONF_API_KEY]
        port = self.config_entry.data[CONF_PORT]
        verify_ssl = self.config_entry.data[CONF_VERIFY_SSL]

        (base_url, path) = extract_base_url_and_path(url)

        self.grocy_api = Grocy(
            base_url, api_key, path=path, port=port, verify_ssl=verify_ssl
        )
        self.grocy_data = GrocyData(hass, self.grocy_api)

        self.available_entities: list[str] = []
        self.entities: list[Entity] = []

    async def _async_update_data(self) -> GrocyCoordinatorData:
        """Fetch data."""
        data = GrocyCoordinatorData()
        for entity in self.entities:
            if not entity.enabled:
                _LOGGER.debug("Entity %s is disabled", entity.entity_id)
                continue

            try:
                data[
                    entity.entity_description.key
                ] = await self.grocy_data.async_update_data(
                    entity.entity_description.key
                )
            except Exception as error:  # pylint: disable=broad-except
                raise UpdateFailed(f"Update failed: {error}") from error

        return data
