"""Binary sensor platform for blueprint."""
import logging
from homeassistant.components.binary_sensor import BinarySensorDevice

# pylint: disable=relative-beyond-top-level
from .const import (
    BINARY_SENSOR,
    DEFAULT_NAME,
    DOMAIN,
    BINARY_SENSOR_TYPES,
    CONF_ALLOW_STOCK,
    DEFAULT_CONF_ALLOW_STOCK,
    EXPIRING_PRODUCTS_NAME,
    EXPIRED_PRODUCTS_NAME,
    MISSING_PRODUCTS_NAME,
    STOCK_NAME,
)
from .entity import GrocyEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup binary_sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    options_allow_stock = entry.options.get(CONF_ALLOW_STOCK, DEFAULT_CONF_ALLOW_STOCK)
    for binary_sensor in BINARY_SENSOR_TYPES:
        if options_allow_stock and binary_sensor.startswith(EXPIRING_PRODUCTS_NAME):
            _LOGGER.debug("Adding expiring products binary sensor")
            device_name = STOCK_NAME
            async_add_entities(
                [GrocyBinarySensor(coordinator, entry, device_name, binary_sensor)],
                True,
            )
        elif options_allow_stock and binary_sensor.startswith(EXPIRED_PRODUCTS_NAME):
            _LOGGER.debug("Adding expired products binary sensor")
            device_name = STOCK_NAME
            async_add_entities(
                [GrocyBinarySensor(coordinator, entry, device_name, binary_sensor)],
                True,
            )
        elif options_allow_stock and binary_sensor.startswith(MISSING_PRODUCTS_NAME):
            _LOGGER.debug("Adding missing products binary sensor")
            device_name = STOCK_NAME
            async_add_entities(
                [GrocyBinarySensor(coordinator, entry, device_name, binary_sensor)],
                True,
            )


class GrocyBinarySensor(GrocyEntity, BinarySensorDevice):
    """Grocy binary_sensor class."""

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        return f"{DEFAULT_NAME}_{BINARY_SENSOR}"

    @property
    def device_class(self):
        """Return the class of this binary_sensor."""
        return None

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return True
        # return self.coordinator.data.get("bool_on", False)
