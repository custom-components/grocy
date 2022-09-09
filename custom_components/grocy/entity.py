"""Entity for Grocy."""
from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, Entity, EntityDescription

from .const import DOMAIN, GROCY_CLIENT, NAME, VERSION
from .grocy_data import GrocyData
from .json_encoder import CustomJSONEncoder

_LOGGER = logging.getLogger(__name__)


class GrocyEntity(Entity):
    """Grocy base entity definition."""

    def __init__(
        self,
        hass: HomeAssistant,
        description: EntityDescription,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize entity."""
        self._attr_name = description.name
        self._attr_unique_id = f"{config_entry.entry_id}{description.key.lower()}"
        self.entity_description: EntityDescription = description
        self.config_entry: ConfigEntry = config_entry
        self.grocy_client: GrocyData = hass.data[DOMAIN][GROCY_CLIENT]
        self.data: List[Any] = []

    async def async_update(self) -> None:
        """Update Grocy entity."""
        if not self.enabled:
            return

        try:
            self.data = await self.entity_description.value_fn(self.grocy_client)
            self._attr_available = True
        except Exception as error:  # pylint: disable=broad-except
            self.data = []
            if self._attr_available:
                _LOGGER.error("An error occurred while updating sensor", exc_info=error)
            self._attr_available = False

    @property
    def device_info(self) -> DeviceInfo:
        """Grocy device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=NAME,
            manufacturer=NAME,
            software_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the extra state attributes."""
        data = self.data
        if data and hasattr(self.entity_description, "attributes_fn"):
            return json.loads(
                json.dumps(
                    self.entity_description.attributes_fn(data),
                    cls=CustomJSONEncoder,
                )
            )

        return None
