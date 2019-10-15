"""Binary sensor platform for grocy."""
from homeassistant.components.binary_sensor import BinarySensorDevice
from .const import (
    ATTRIBUTION,
    DEFAULT_NAME,
    DOMAIN_DATA,
    DOMAIN,
)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Setup binary_sensor platform."""
    async_add_entities(
        [GrocyExpiringProductsBinarySensor(hass, discovery_info)], True)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    async_add_devices([GrocyExpiringProductsBinarySensor(hass,config_entry)], True)

class GrocyExpiringProductsBinarySensor(BinarySensorDevice):
    """grocy binary_sensor class."""

    def __init__(self, hass, config):
        self.hass = hass
        self.attr = {}
        self._status = False
        self._name = '{}.expiring_products'.format(DEFAULT_NAME)
        self._client = self.hass.data[DOMAIN_DATA]["client"]

    async def async_update(self):
        import jsonpickle
        """Update the binary_sensor."""
        # Send update "signal" to the component
        await self._client.async_update_expiring_products()

        # Get new data (if any)
        expiring_products = (
            self.hass.data[DOMAIN_DATA].get("expiring_products"))

        # Check the data and update the value.
        if not expiring_products:
            self._status = self._status
        else:
            self._status = True

        # Set/update attributes
        self.attr["attribution"] = ATTRIBUTION
        self.attr["items"] = jsonpickle.encode(
            expiring_products,
            unpicklable=False)

    @property
    def unique_id(self):
        """Return a unique ID to use for this binary_sensor."""
        return (
            "e308a906-4c3f-4a58-a067-47d04d3e196e"
        )

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Grocy",
        }

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        return self._name

    @property
    def device_class(self):
        """Return the class of this binary_sensor."""
        return None

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self._status

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attr
