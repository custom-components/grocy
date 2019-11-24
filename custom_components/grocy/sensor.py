"""Sensor platform for grocy."""
from homeassistant.helpers.entity import Entity

from .const import (
    ATTRIBUTION,
    DEFAULT_NAME,
    DOMAIN_DATA,
    ICON,
    SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT,
    SENSOR_CHORES_UNIT_OF_MEASUREMENT,
)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Setup sensor platform."""
    async_add_entities([GrocyProductsSensor(hass, discovery_info)], True)
    async_add_entities([GrocyChoresSensor(hass, discovery_info)], True)


class GrocyProductsSensor(Entity):
    """grocy Sensor class."""

    def __init__(self, hass, config):
        self.hass = hass
        self.attr = {}
        self._state = None
        self._name = '{}.products'.format(config.get("name", DEFAULT_NAME))

    async def async_update(self):
        import jsonpickle
        """Update the sensor."""
        # Send update "signal" to the component
        await self.hass.data[DOMAIN_DATA]["client"].async_update_stock()

        # Get new data (if any)
        stock = self.hass.data[DOMAIN_DATA].get("stock")

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
        return SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attr


class GrocyChoresSensor(Entity):
    """grocy Sensor class."""

    def __init__(self, hass, config):
        self.hass = hass
        self.attr = {}
        self._state = None
        self._name = '{}.chores'.format(config.get("name", DEFAULT_NAME))

    async def async_update(self):
        import jsonpickle
        """Update the sensor."""
        # Send update "signal" to the component
        await self.hass.data[DOMAIN_DATA]["client"].async_update_chores()

        # Get new data (if any)
        chores = self.hass.data[DOMAIN_DATA].get("chores")

        # Check the data and update the value.
        if chores is None:
            self._state = self._state
        else:
            self._state = len(chores)

        # Set/update attributes
        self.attr["attribution"] = ATTRIBUTION
        self.attr["items"] = jsonpickle.encode(chores, unpicklable=False)

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
        return SENSOR_CHORES_UNIT_OF_MEASUREMENT

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attr
