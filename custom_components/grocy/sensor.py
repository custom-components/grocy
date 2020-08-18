"""Sensor platform for grocy."""
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.core import callback

from .const import (
    ATTRIBUTION,
    CHORES_NAME,
    TASKS_NAME,
    MEAL_PLAN_NAME,
    STOCK_NAME,
    SHOPPING_LIST_NAME,
    DEFAULT_CONF_NAME,
    DOMAIN,
    LOGGER,
    ICON,
    SENSOR_CHORES_UNIT_OF_MEASUREMENT,
    SENSOR_TASKS_UNIT_OF_MEASUREMENT,
    SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT,
    SENSOR_MEALS_UNIT_OF_MEASUREMENT,
    SENSOR_TYPES,
    NEW_SENSOR,
)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Setup sensor platform."""

    async_add_entities([GrocySensor(hass, discovery_info)], True)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    instance = hass.data[DOMAIN]["instance"]

    @callback
    def async_add_sensor(new=True):
        LOGGER.debug("Adding sensors")
        entities = []

        for sensor in SENSOR_TYPES:
            if instance.option_allow_chores and sensor.startswith(CHORES_NAME):
                LOGGER.debug("Adding chores sensor.")
                async_add_devices([GrocySensor(hass, sensor)], True)
            elif instance.option_allow_meal_plan and sensor.startswith(MEAL_PLAN_NAME):
                LOGGER.debug("Adding meal plan sensor.")
                async_add_devices([GrocySensor(hass, sensor)], True)
            elif instance.option_allow_shopping_list and sensor.startswith(
                SHOPPING_LIST_NAME
            ):
                LOGGER.debug("Adding shopping list sensor.")
                async_add_devices([GrocySensor(hass, sensor)], True)
            elif instance.option_allow_stock and sensor.startswith(STOCK_NAME):
                LOGGER.debug("Adding stock sensor.")
                async_add_devices([GrocySensor(hass, sensor)], True)
            elif instance.option_allow_tasks and sensor.startswith(TASKS_NAME):
                LOGGER.debug("Adding tasks sensor.")
                async_add_devices([GrocySensor(hass, sensor)], True)

    instance.listeners.append(
        async_dispatcher_connect(
            hass, instance.async_signal_new_device(NEW_SENSOR), async_add_sensor
        )
    )

    async_add_sensor()


class GrocySensor(Entity):
    """grocy Sensor class."""

    def __init__(self, hass, sensor_type):
        self.hass = hass
        self.sensor_type = sensor_type
        self.attr = {}
        self._state = None
        self._hash_key = self.hass.data[DOMAIN].get("hash_key")
        self._unique_id = "{}-{}".format(self._hash_key, self.sensor_type)
        self._name = "{}.{}".format(DEFAULT_CONF_NAME, self.sensor_type)

    async def async_update(self):
        """Update the sensor."""
        # Send update "signal" to the component
        await self.hass.data[DOMAIN]["client"].async_update_data(self.sensor_type)

        self.attr["items"] = [
            x.as_dict() for x in self.hass.data[DOMAIN].get(self.sensor_type, [])
        ]
        self._state = len(self.attr["items"])
        # LOGGER.debug(self.attr)

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
        elif self.sensor_type == TASKS_NAME:
            return SENSOR_TASKS_UNIT_OF_MEASUREMENT
        elif self.sensor_type == MEAL_PLAN_NAME:
            return SENSOR_MEALS_UNIT_OF_MEASUREMENT
        else:
            return SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attr

