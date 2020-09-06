"""Sensor platform for Grocy."""

import logging

from .const import DOMAIN, GrocyEntityType
from .entity import GrocyEntity

_LOGGER = logging.getLogger(__name__)
SENSOR_TYPES = [
    GrocyEntityType.CHORES,
    GrocyEntityType.MEAL_PLAN,
    GrocyEntityType.SHOPPING_LIST,
    GrocyEntityType.STOCK,
    GrocyEntityType.TASKS,
]


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN]

    entities = []
    for sensor in SENSOR_TYPES:
        _LOGGER.debug("Adding %s sensor", sensor)
        entity = GrocySensor(coordinator, entry, sensor)
        coordinator.entities.append(entity)
        entities.append(entity)

    async_add_entities(entities, True)


class GrocySensor(GrocyEntity):
    """Grocy Sensor class."""

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self.entity_data:
            return
        return len(self.entity_data)
