"""Sensor platform for grocy."""
import logging
from homeassistant.helpers.entity import Entity

from .const import (
    ATTRIBUTION,
    CHORES_NAME,
    DEFAULT_NAME,
    DOMAIN,
    DOMAIN_DATA,
    ICON,
    SENSOR_CHORES_UNIT_OF_MEASUREMENT,
    SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT,
    SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Setup sensor platform."""

    async_add_entities([GrocySensor(hass, discovery_info)], True)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    for sensor in SENSOR_TYPES:
        async_add_devices([GrocySensor(hass, sensor)], True)


class GrocySensor(Entity):
    """grocy Sensor class."""

    def __init__(self, hass, sensor_type):
        self.hass = hass
        self.sensor_type = sensor_type
        self.attr = {}
        self._state = None
        self._hash_key = self.hass.data[DOMAIN_DATA]["hash_key"]
        self._unique_id = "{}-{}".format(self._hash_key, self.sensor_type)
        self._name = "{}.{}".format(DEFAULT_NAME, self.sensor_type)

    async def async_update(self):
        """Update the sensor."""
        # Send update "signal" to the component
        await self.hass.data[DOMAIN_DATA]["client"].async_update_data(self.sensor_type)

        self.attr["items"] = [
            x.as_dict() for x in self.hass.data[DOMAIN_DATA].get(self.sensor_type, [])
        ]
        self._state = len(self.attr["items"])
        _LOGGER.debug(self.attr)

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return self._unique_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self._name,
            "manufacturer": "Grocy",
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def unit_of_measurement(self):
        if self.sensor_type == CHORES_NAME:
            return SENSOR_CHORES_UNIT_OF_MEASUREMENT
        else:
            return SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attr

