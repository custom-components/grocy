"""GrocyEntity class"""
from homeassistant.helpers import entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

# pylint: disable=relative-beyond-top-level
from .const import (
    DOMAIN,
    GrocyEntityIcon,
    GrocyEntityType,
    GrocyEntityUnit,
    NAME,
    VERSION,
)


class GrocyCoordinatorEntity(entity.Entity):
    """
    CoordinatorEntity was added to HA in 0.115, this is a  copy of the
    class CoordinatorEntity from homeassistant.helpers.update_coordinator

    Remove this class and use CoordinatorEntity instead when grocy require min version 0.115
    """

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        self.coordinator = coordinator

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Update the entity.

        Only used by the generic entity update service.
        """

        # Ignore manual update requests if the entity is disabled
        if not self.enabled:
            return

        await self.coordinator.async_request_refresh()


class GrocyEntity(GrocyCoordinatorEntity):
    def __init__(self, coordinator, config_entry, entity_type):
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
        elif self.entity_type == GrocyEntityType.CHORES:
            return {"chores": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.EXPIRED_PRODUCTS:
            return {"expired": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.EXPIRING_PRODUCTS:
            return {"expiring": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.MEAL_PLAN:
            return {"meals": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.MISSING_PRODUCTS:
            return {"missing": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.OVERDUE_CHORES:
            return {"chores": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.OVERDUE_TASKS:
            return {"tasks": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.PRODUCTS:
            return {"products": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.SHOPPING_LIST:
            return {"products": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.STOCK:
            return {"products": [x.as_dict() for x in self.entity_data]}
        elif self.entity_type == GrocyEntityType.TASKS:
            return {"tasks": [x.as_dict() for x in self.entity_data]}
