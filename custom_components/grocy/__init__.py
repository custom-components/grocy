"""
Custom integration to integrate Grocy with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/grocy
"""
import asyncio
import logging
from datetime import timedelta
from typing import List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pygrocy import Grocy

from .const import (
    CONF_API_KEY,
    CONF_PORT,
    CONF_URL,
    CONF_VERIFY_SSL,
    DOMAIN,
    GrocyEntityType,
    PLATFORMS,
    STARTUP_MESSAGE,
)
from .grocy_data import GrocyData, async_setup_image_api
from .services import async_setup_services, async_unload_services

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


async def async_setup(_hass: HomeAssistant, _config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info(STARTUP_MESSAGE)

    coordinator = GrocyDataUpdateCoordinator(
        hass,
        config_entry.data[CONF_URL],
        config_entry.data[CONF_API_KEY],
        config_entry.data[CONF_PORT],
        config_entry.data[CONF_VERIFY_SSL],
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN] = coordinator

    for platform in PLATFORMS:
        hass.async_add_job(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    await async_setup_services(hass, config_entry)

    # Setup http endpoint for proxying images from grocy
    await async_setup_image_api(hass, config_entry.data)

    config_entry.add_update_listener(async_reload_entry)
    return True


class GrocyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, url, api_key, port_number, verify_ssl):
        """Initialize."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = Grocy(url, api_key, port_number, verify_ssl)
        self.entities = []
        self.data = {}

    async def _async_update_data(self):
        """Update data via library."""
        grocy_data = GrocyData(self.hass, self.api)
        data = {}
        features = []
        try:
            features = await async_supported_features(grocy_data)
            if not features:
                raise UpdateFailed("No features enabled")
        except Exception as exception:
            raise UpdateFailed(exception)

        for entity in self.entities:
            if entity.enabled and entity.entity_type in features:
                try:
                    data[entity.entity_type] = await grocy_data.async_update_data(
                        entity.entity_type
                    )
                except Exception as exception:
                    _LOGGER.error(
                        f"Update of {entity.entity_type} failed with {exception}"
                    )
            elif entity.entity_type not in features:
                _LOGGER.warning(
                    f"You have enabled the entity for {entity.name}, but this feature is not enabled in Grocy",
                )
        return data


async def async_supported_features(grocy_data) -> List[str]:
    """Return a list of supported features."""
    features = []
    config = await grocy_data.async_get_config()
    if config:
        if config["FEATURE_FLAG_STOCK"] != "0":
            features.append(GrocyEntityType.STOCK)
            features.append(GrocyEntityType.PRODUCTS)
            features.append(GrocyEntityType.MISSING_PRODUCTS)
            features.append(GrocyEntityType.EXPIRED_PRODUCTS)
            features.append(GrocyEntityType.EXPIRING_PRODUCTS)

        if config["FEATURE_FLAG_SHOPPINGLIST"] != "0":
            features.append(GrocyEntityType.SHOPPING_LIST)

        if config["FEATURE_FLAG_TASKS"] != "0":
            features.append(GrocyEntityType.TASKS)
            features.append(GrocyEntityType.OVERDUE_TASKS)

        if config["FEATURE_FLAG_CHORES"] != "0":
            features.append(GrocyEntityType.CHORES)
            features.append(GrocyEntityType.OVERDUE_CHORES)

        if config["FEATURE_FLAG_RECIPES"] != "0":
            features.append(GrocyEntityType.MEAL_PLAN)

    return features


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    _LOGGER.debug("Unloading with state %s", entry.state)
    if entry.state == "loaded":
        unloaded = all(
            await asyncio.gather(
                *[
                    hass.config_entries.async_forward_entry_unload(entry, platform)
                    for platform in PLATFORMS
                ]
            )
        )
        _LOGGER.debug("Unloaded? %s", unloaded)
        del hass.data[DOMAIN]
        return unloaded
    return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    unloaded = await async_unload_entry(hass, entry)
    _LOGGER.error("Unloaded successfully: %s", unloaded)
    if unloaded:
        await async_setup_entry(hass, entry)
        await async_unload_services(hass)
