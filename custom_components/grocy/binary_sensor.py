"""Binary sensor platform for blueprint."""
import logging
from homeassistant.components.binary_sensor import BinarySensorDevice

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


class GrocyBinarySensor(GrocyEntity, BinarySensorDevice):
    """Grocy binary_sensor class."""

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        if not self.entity_data:
            return

        elif self.entity_type == GrocyEntityType.MISSING_PRODUCTS:
            return len(self.entity_data) > 0
        elif self.entity_type == GrocyEntityType.EXPIRING_PRODUCTS:
            return len(self.entity_data) > 0
        elif self.entity_type == GrocyEntityType.EXPIRED_PRODUCTS:
            return len(self.entity_data) > 0
