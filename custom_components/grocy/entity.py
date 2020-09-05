"""GrocyEntity class"""
from homeassistant.helpers import entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

# pylint: disable=relative-beyond-top-level
from .const import (
    DOMAIN,
    GrocyEntityIcon,
    GrocyEntityType,
    GrocyEntityUnit,
    NAME,
    VERSION,
)


class GrocyEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry, entity_type):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.entity_type = entity_type

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}{self.entity_type.lower()}"

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        return f"{NAME} {self.entity_type.lower().replace('_', ' ')}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return False

    @property
    def entity_data(self):
        """Return the entity_data of the entity."""
        return self.coordinator.data.get(self.entity_type)

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        if GrocyEntityType(self.entity_type).name in [x.name for x in GrocyEntityUnit]:
            return GrocyEntityUnit[GrocyEntityType(self.entity_type).name]

    @property
    def icon(self):
        """Return the icon of the entity."""
        if GrocyEntityType(self.entity_type).name in [x.name for x in GrocyEntityIcon]:
            return GrocyEntityIcon[GrocyEntityType(self.entity_type).name]

        return GrocyEntityIcon.DEFAULT

    @property
    def device_info(self):
        return {
            # "identifiers": {(DOMAIN, self.unique_id)},
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "entry_type": "service",
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if not self.entity_data:
            return

        elif self.entity_type == GrocyEntityType.TASKS:
            return {"tasks": [x.as_dict() for x in self.entity_data]}

        elif self.entity_type == GrocyEntityType.MISSING_PRODUCTS:
            return {"missing": [x.as_dict() for x in self.entity_data]}
