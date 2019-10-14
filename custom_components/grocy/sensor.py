"""Sensor platform for grocy."""
from homeassistant.helpers.entity import Entity
import logging

from .const import (
    ATTRIBUTION,
    DEFAULT_NAME,
    DOMAIN,
    DOMAIN_DATA,
    ICON,
    SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT,
    SENSOR_CHORES_UNIT_OF_MEASUREMENT,
    SENSOR_TYPE,
    CONF_SENSOR,
    CONF_CHORES_NAME,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Setup sensor platform."""
    sensor_list = hass.data[DOMAIN_DATA].get(CONF_SENSOR)
    
    for sensor in sensor_list:
        async_add_entities([GrocySensor(hass, discovery_info, type = sensor)], True)
    


class GrocySensor(Entity):
    """grocy Sensor class."""

    def __init__(self, hass, config, type):
        self.hass = hass
        self._type = type
        self.attr = {}
        self._state = None
        self._name = '{}.{}'.format(DEFAULT_NAME, self._type)

    async def async_update(self):
        import jsonpickle
        """Update the sensor."""
        # Send update "signal" to the component
        await self.hass.data[DOMAIN_DATA]["client"].async_update_data(self._type)

        # Get new data (if any)
        stock = self.hass.data[DOMAIN_DATA].get(self._type)

        # Check the data and update the value.
        if stock is None:
            self._state = self._state
        else:
            self._state = len(stock)

        # Set/update attributes
        self.attr["attribution"] = ATTRIBUTION
        self.attr["items"] = jsonpickle.encode(stock, unpicklable=False)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def unit_of_measurement(self):
        if self._type == CONF_CHORES_NAME:
            return SENSOR_CHORES_UNIT_OF_MEASUREMENT
        else:
            return SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attr


