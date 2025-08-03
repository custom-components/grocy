"""Custom field sensor for Grocy equipment."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_EQUIPMENT, DOMAIN
from .coordinator import GrocyDataUpdateCoordinator
from .entity import GrocyEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class EquipmentCustomFieldSensorDescription(SensorEntityDescription):
    """Sensor entity description for equipment custom fields."""

    equipment_id: int | None = None
    field_name: str | None = None
    field_value_fn: Callable[[Any], Any] | None = None
    native_unit_of_measurement: str | None = None
    icon: str | None = "mdi:tools"


async def async_setup_equipment_custom_fields(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up equipment custom field sensors."""
    coordinator: GrocyDataUpdateCoordinator = hass.data[DOMAIN]

    if ATTR_EQUIPMENT not in coordinator.available_entities:
        return

    # Get equipment data to discover custom fields
    equipment_data = coordinator.data.get(ATTR_EQUIPMENT, [])
    if not equipment_data:
        try:
            # Force an update to get equipment data if not available
            _LOGGER.debug("Equipment data not available, fetching directly")
            equipment_data = await hass.async_add_executor_job(
                coordinator.grocy_data.api.equipment, None, True
            )

            # Store the data in coordinator for future use
            coordinator.data[ATTR_EQUIPMENT] = equipment_data
        except Exception as error:
            _LOGGER.error("Error fetching equipment data: %s", error)
            return

    entities = []

    for equipment_item in equipment_data:
        if not hasattr(equipment_item, "userfields") or not equipment_item.userfields:
            continue

        for field_name, field_value in equipment_item.userfields.items():
            # Skip empty fields
            if field_value is None or field_value == "":
                continue

            # Determine field type and icon
            icon = "mdi:tools"
            native_unit = None

            # Try to infer field type and unit
            if isinstance(field_value, bool):
                icon = "mdi:checkbox-marked" if field_value else "mdi:checkbox-blank-outline"
            elif isinstance(field_value, (int, float)):
                icon = "mdi:numeric"
            elif isinstance(field_value, str):
                if "temperature" in field_name.lower():
                    icon = "mdi:thermometer"
                    native_unit = "°C"
                elif "voltage" in field_name.lower() or "volt" in field_name.lower():
                    icon = "mdi:flash"
                    native_unit = "V"
                elif "power" in field_name.lower() or "watt" in field_name.lower():
                    icon = "mdi:power-plug"
                    native_unit = "W"
                elif "weight" in field_name.lower():
                    icon = "mdi:weight"
                    native_unit = "kg"
                elif "length" in field_name.lower() or "width" in field_name.lower() or "height" in field_name.lower():
                    icon = "mdi:ruler"
                    native_unit = "m"
                elif "date" in field_name.lower():
                    icon = "mdi:calendar"

            description = EquipmentCustomFieldSensorDescription(
                key=f"equipment_{equipment_item.id}_{field_name}",
                name=f"{equipment_item.name} {field_name}",
                equipment_id=equipment_item.id,
                field_name=field_name,
                field_value_fn=lambda data, e_id=equipment_item.id, f_name=field_name: _get_field_value(data, e_id, f_name),
                native_unit_of_measurement=native_unit,
                icon=icon,
            )

            entity = EquipmentCustomFieldSensor(coordinator, description, config_entry)
            coordinator.entities.append(entity)
            entities.append(entity)

    await async_add_entities(entities, True)


def _get_field_value(data, equipment_id, field_name):
    """Get the value of a specific field for an equipment item."""
    for equipment in data:
        if equipment.id == equipment_id:
            if hasattr(equipment, "userfields") and equipment.userfields:
                return equipment.userfields.get(field_name)
    return None


class EquipmentCustomFieldSensor(GrocyEntity, SensorEntity):
    """Sensor for equipment custom fields."""

    entity_description: EquipmentCustomFieldSensorDescription

    @property
    def native_value(self):
        """Return the value of the custom field."""
        entity_data = self.coordinator.data.get(ATTR_EQUIPMENT, [])
        if entity_data and self.entity_description.field_value_fn:
            return self.entity_description.field_value_fn(entity_data)
        return None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional attributes for the sensor."""
        entity_data = self.coordinator.data.get(ATTR_EQUIPMENT, [])
        if not entity_data:
            return None

        for equipment in entity_data:
            if equipment.id == self.entity_description.equipment_id:
                return {
                    "equipment_name": equipment.name,
                    "equipment_id": equipment.id,
                    "field_name": self.entity_description.field_name,
                }

        return None
