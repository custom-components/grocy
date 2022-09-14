"""Binary sensor platform for Grocy."""
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Coroutine, List

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
    GROCY_AVAILABLE_ENTITIES,
    REGISTERED_ENTITIES,
)
from .entity import GrocyEntity
from .grocy_data import GrocyData

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=300)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup binary sensor platform."""
    available_entities = hass.data[DOMAIN][GROCY_AVAILABLE_ENTITIES]
    registered_entities = hass.data[DOMAIN][REGISTERED_ENTITIES]
    entities = []
    for description in BINARY_SENSORS:
        if description.exists_fn(available_entities):
            entity = GrocyBinarySensorEntity(hass, description, config_entry)
            entities.append(entity)
            registered_entities.append(entity)
        else:
            _LOGGER.debug(
                "Entity description '%s' is not available.",
                description.key,
            )

    async_add_entities(entities, True)


@dataclass
class GrocyEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[[GrocyData], Coroutine[Any, Any, Any]]


@dataclass
class GrocyBinarySensorEntityDescription(
    BinarySensorEntityDescription, GrocyEntityDescriptionMixin
):
    """Grocy binary sensor entity description."""

    attributes_fn: Callable[[List[Any]], Mapping[str, Any] | None] = lambda _: None
    exists_fn: Callable[[List[str]], bool] = lambda _: True
    entity_registry_enabled_default: bool = False


BINARY_SENSORS: tuple[GrocyBinarySensorEntityDescription, ...] = (
    GrocyBinarySensorEntityDescription(
        key=ATTR_EXPIRED_PRODUCTS,
        name="Grocy expired products",
        icon="mdi:delete-alert-outline",
        exists_fn=lambda entities: ATTR_EXPIRED_PRODUCTS in entities,
        value_fn=lambda grocy: grocy.async_update_expired_products(),
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
        value_fn=lambda grocy: grocy.async_update_expiring_products(),
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
        value_fn=lambda grocy: grocy.async_update_overdue_products(),
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
        value_fn=lambda grocy: grocy.async_update_missing_products(),
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
        value_fn=lambda grocy: grocy.async_update_overdue_chores(),
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
        value_fn=lambda grocy: grocy.async_update_overdue_tasks(),
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
        value_fn=lambda grocy: grocy.async_update_batteries(),
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
        return len(self.data) > 0 if self.data else False
