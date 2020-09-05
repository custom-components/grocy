"""GrocyEntity class"""
from homeassistant.helpers import entity

# pylint: disable=relative-beyond-top-level
from .const import DOMAIN, NAME, VERSION


class GrocyEntity(entity.Entity):
    def __init__(self, coordinator, config_entry, device_name, sensor_type):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.device_name = device_name
        self.sensor_type = sensor_type

        self._unique_id = "{}-{}".format(self.coordinator.hash_key, self.sensor_type)

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self._unique_id

    @property
    def device_info(self):
        return {
            # "identifiers": {(DOMAIN, self.unique_id)},
            "identifiers": {(DOMAIN, self.device_name)},
            "name": self.device_name,
            "model": VERSION,
            "manufacturer": NAME,
            "entry_type": "service",
        }

    # @property
    # def device_state_attributes(self):
    #     """Return the state attributes."""
    #     return {
    #         "time": str(self.coordinator.data.get("time")),
    #         "static": self.coordinator.data.get("static"),
    #     }

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Grocy entity."""
        await self.coordinator.async_request_refresh()
