"""GrocyEntity class"""
import json

from homeassistant.helpers.device_registry import DeviceEntryType
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
from .json_encode import GrocyJSONEncoder


class GrocyEntity(CoordinatorEntity):
    """Base class for Grocy entities."""

    def __init__(self, coordinator, config_entry, entity_type):
        """Initialize generic Grocy entity."""
        super().__init__(coordinator)
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
        if self.coordinator.data is None:
            return None
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
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.entity_data:
            return

        data = {}

        if self.entity_type == GrocyEntityType.CHORES:
            data = {"chores": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.EXPIRED_PRODUCTS:
            data = {"expired": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.EXPIRING_PRODUCTS:
            data = {"expiring": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.MEAL_PLAN:
            data = {"meals": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.MISSING_PRODUCTS:
            data = {"missing": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.OVERDUE_CHORES:
            data = {"chores": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.OVERDUE_TASKS:
            data = {"tasks": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.PRODUCTS:
            data = {"products": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.SHOPPING_LIST:
            data = {"products": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.STOCK:
            data = {"products": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.TASKS:
            data = {"tasks": [x.as_dict() for x in self.entity_data]}

        if data:
            data["count"] = sum(len(entry) for entry in data.values())

        return json.loads(json.dumps(data, cls=GrocyJSONEncoder))
