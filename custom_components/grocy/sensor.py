"""Sensor platform for Grocy."""
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Coroutine, List

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    ATTR_BATTERIES,
    ATTR_CHORES,
    ATTR_MEAL_PLAN,
    ATTR_SHOPPING_LIST,
    ATTR_STOCK,
    ATTR_TASKS,
    CHORES,
    DOMAIN,
    GROCY_AVAILABLE_ENTITIES,
    ITEMS,
    MEAL_PLANS,
    PRODUCTS,
    REGISTERED_ENTITIES,
    TASKS,
)
from .entity import GrocyEntity
from .grocy_data import GrocyData

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup sensor platform."""
    available_entities = hass.data[DOMAIN][GROCY_AVAILABLE_ENTITIES]
    registered_entities = hass.data[DOMAIN][REGISTERED_ENTITIES]
    entities = []
    for description in SENSORS:
        if description.exists_fn(available_entities):
            entity = GrocySensorEntity(hass, description, config_entry)
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
class GrocySensorEntityDescription(
    SensorEntityDescription, GrocyEntityDescriptionMixin
):
    """Grocy sensor entity description."""

    attributes_fn: Callable[[List[Any]], Mapping[str, Any] | None] = lambda _: None
    exists_fn: Callable[[List[str]], bool] = lambda _: True
    entity_registry_enabled_default: bool = False


SENSORS: tuple[GrocySensorEntityDescription, ...] = (
    GrocySensorEntityDescription(
        key=ATTR_CHORES,
        name="Grocy chores",
        native_unit_of_measurement=CHORES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:broom",
        exists_fn=lambda entities: ATTR_CHORES in entities,
        value_fn=lambda grocy: grocy.async_update_chores(),
        attributes_fn=lambda data: {
            "chores": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocySensorEntityDescription(
        key=ATTR_MEAL_PLAN,
        name="Grocy meal plan",
        native_unit_of_measurement=MEAL_PLANS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:silverware-variant",
        exists_fn=lambda entities: ATTR_MEAL_PLAN in entities,
        value_fn=lambda grocy: grocy.async_update_meal_plan(),
        attributes_fn=lambda data: {
            "meals": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocySensorEntityDescription(
        key=ATTR_SHOPPING_LIST,
        name="Grocy shopping list",
        native_unit_of_measurement=PRODUCTS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cart-outline",
        exists_fn=lambda entities: ATTR_SHOPPING_LIST in entities,
        value_fn=lambda grocy: grocy.async_update_shopping_list(),
        attributes_fn=lambda data: {
            "products": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocySensorEntityDescription(
        key=ATTR_STOCK,
        name="Grocy stock",
        native_unit_of_measurement=PRODUCTS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fridge-outline",
        exists_fn=lambda entities: ATTR_STOCK in entities,
        value_fn=lambda grocy: grocy.async_update_stock(),
        attributes_fn=lambda data: {
            "products": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocySensorEntityDescription(
        key=ATTR_TASKS,
        name="Grocy tasks",
        native_unit_of_measurement=TASKS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:checkbox-marked-circle-outline",
        exists_fn=lambda entities: ATTR_TASKS in entities,
        value_fn=lambda grocy: grocy.async_update_tasks(),
        attributes_fn=lambda data: {
            "tasks": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
    GrocySensorEntityDescription(
        key=ATTR_BATTERIES,
        name="Grocy batteries",
        native_unit_of_measurement=ITEMS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        exists_fn=lambda entities: ATTR_BATTERIES in entities,
        value_fn=lambda grocy: grocy.async_update_batteries(),
        attributes_fn=lambda data: {
            "batteries": [x.as_dict() for x in data],
            "count": len(data),
        },
    ),
)


class GrocySensorEntity(GrocyEntity, SensorEntity):
    """Grocy sensor entity definition."""

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return len(self.data) if self.data else 0
