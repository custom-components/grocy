"""Binary sensor platform for Grocy."""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity

# pylint: disable=relative-beyond-top-level
from .const import (
    DOMAIN,
    GrocyEntityType,
)
from .entity import GrocyEntity

_LOGGER = logging.getLogger(__name__)
BINARY_SENSOR_TYPES = [
    GrocyEntityType.EXPIRED_PRODUCTS,
    GrocyEntityType.EXPIRING_PRODUCTS,
    GrocyEntityType.MISSING_PRODUCTS,
    GrocyEntityType.OVERDUE_CHORES,
    GrocyEntityType.OVERDUE_TASKS,
]


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup binary_sensor platform."""
    coordinator = hass.data[DOMAIN]

    entities = []
    for binary_sensor in BINARY_SENSOR_TYPES:
        _LOGGER.debug("Adding %s binary sensor", binary_sensor)
        entity = GrocyBinarySensor(coordinator, entry, binary_sensor)
        coordinator.entities.append(entity)
        entities.append(entity)

    async_add_entities(entities, True)


class GrocyBinarySensor(GrocyEntity, BinarySensorEntity):
    """Grocy binary_sensor class."""

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        if not self.entity_data:
            return

        return len(self.entity_data) > 0
