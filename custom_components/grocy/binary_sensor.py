"""Binary sensor platform for grocy."""
from homeassistant.components.binary_sensor import BinarySensorDevice

from .const import (ATTRIBUTION, BINARY_SENSOR_TYPES, DEFAULT_NAME, DOMAIN,
                    DOMAIN_DATA)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Setup binary_sensor platform."""
    async_add_entities(
        [GrocyBinarySensor(hass, discovery_info)], True)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    for binary_sensor in BINARY_SENSOR_TYPES:
        async_add_devices([GrocyBinarySensor(hass, binary_sensor)], True)

class GrocyBinarySensor(BinarySensorDevice):
    """grocy binary_sensor class."""

    def __init__(self, hass, sensor_type):
        self.hass = hass
        self.sensor_type = sensor_type
        self.attr = {}
        self._status = False
        self._hash_key = self.hass.data[DOMAIN_DATA]["hash_key"]
        self._unique_id = '{}-{}'.format(self._hash_key , self.sensor_type)
        self._name = '{}.{}'.format(DEFAULT_NAME, self.sensor_type)
        self._client = self.hass.data[DOMAIN_DATA]["client"]

    async def async_update(self):
        """Update the binary_sensor."""
        # Send update "signal" to the component
        await self._client.async_update_data(self.sensor_type)

        # Get new data (if any)
        data = []
        items = self.hass.data[DOMAIN_DATA].get(self.sensor_type)

        # Check the data and update the value.
        if not items:
            self._status = self._status
        else:
            self._status = True
            for item in items:
                item_dict = vars(item)
                if '_product' in item_dict and hasattr(item_dict['_product'], '__dict__'):
                    item_dict['_product'] = vars(item_dict['_product'])
                if '_last_done_by' in item_dict and hasattr(item_dict['_last_done_by'], '__dict__'):
                    item_dict['_last_done_by'] = vars(item_dict['_last_done_by'])
                data.append(item_dict)

        # Set/update attributes
        self.attr["attribution"] = ATTRIBUTION
        self.attr["items"] = data

    @property
    def unique_id(self):
        """Return a unique ID to use for this binary_sensor."""
        return self._unique_id

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

        """Return the state attributes."""
        return self.attr
