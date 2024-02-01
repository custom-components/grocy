"""Binary sensor platform for Grocy."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_EXPIRED_PRODUCTS,
    ATTR_EXPIRING_PRODUCTS,
    ATTR_MISSING_PRODUCTS,
    ATTR_OVERDUE_BATTERIES,
    ATTR_OVERDUE_CHORES,
    ATTR_OVERDUE_PRODUCTS,
    ATTR_OVERDUE_TASKS,
    DOMAIN,
)
from .coordinator import GrocyCoordinatorData, GrocyDataUpdateCoordinator
from .entity import GrocyEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Initialize binary sensor platform."""
    coordinator: GrocyDataUpdateCoordinator = hass.data[DOMAIN]
    entities = []
    for description in BINARY_SENSORS:
        if description.exists_fn(coordinator.available_entities):
            entity = GrocyBinarySensorEntity(coordinator, description, config_entry)
            coordinator.entities.append(entity)
            entities.append(entity)
        else:
            _LOGGER.debug(
                "Entity description '%s' is not available.",
                description.key,
            )

    async_add_entities(entities, True)


@dataclass
class GrocyBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Grocy binary sensor entity description."""

    attributes_fn: Callable[[list[Any]], GrocyCoordinatorData | None] = lambda _: None
    exists_fn: Callable[[list[str]], bool] = lambda _: True
    entity_registry_enabled_default: bool = False


BINARY_SENSORS: tuple[GrocyBinarySensorEntityDescription, ...] = (
    GrocyBinarySensorEntityDescription(
        key=ATTR_EXPIRED_PRODUCTS,
        name="Grocy expired products",
        icon="mdi:delete-alert-outline",
        exists_fn=lambda entities: ATTR_EXPIRED_PRODUCTS in entities,
        attributes_fn=lambda data: {
            "expired_products": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocyBinarySensorEntityDescription(
        key=ATTR_EXPIRING_PRODUCTS,
        name="Grocy expiring products",
        icon="mdi:clock-fast",
        exists_fn=lambda entities: ATTR_EXPIRING_PRODUCTS in entities,
        attributes_fn=lambda data: {
            "expiring_products": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocyBinarySensorEntityDescription(
        key=ATTR_OVERDUE_PRODUCTS,
        name="Grocy overdue products",
        icon="mdi:alert-circle-check-outline",
        exists_fn=lambda entities: ATTR_OVERDUE_PRODUCTS in entities,
        attributes_fn=lambda data: {
            "overdue_products": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocyBinarySensorEntityDescription(
        key=ATTR_MISSING_PRODUCTS,
        name="Grocy missing products",
        icon="mdi:flask-round-bottom-empty-outline",
        exists_fn=lambda entities: ATTR_MISSING_PRODUCTS in entities,
        attributes_fn=lambda data: {
            "missing_products": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocyBinarySensorEntityDescription(
        key=ATTR_OVERDUE_CHORES,
        name="Grocy overdue chores",
        icon="mdi:alert-circle-check-outline",
        exists_fn=lambda entities: ATTR_OVERDUE_CHORES in entities,
        attributes_fn=lambda data: {
            "overdue_chores": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocyBinarySensorEntityDescription(
        key=ATTR_OVERDUE_TASKS,
        name="Grocy overdue tasks",
        icon="mdi:alert-circle-check-outline",
        exists_fn=lambda entities: ATTR_OVERDUE_TASKS in entities,
        attributes_fn=lambda data: {
            "overdue_tasks": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocyBinarySensorEntityDescription(
        key=ATTR_OVERDUE_BATTERIES,
        name="Grocy overdue batteries",
        icon="mdi:battery-charging-10",
        exists_fn=lambda entities: ATTR_OVERDUE_BATTERIES in entities,
        attributes_fn=lambda data: {
            "overdue_batteries": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
)


class GrocyBinarySensorEntity(GrocyEntity, BinarySensorEntity):
    """Grocy binary sensor entity definition."""

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        entity_data = self.coordinator.data[self.entity_description.key]

        return len(entity_data) > 0 if entity_data else False
