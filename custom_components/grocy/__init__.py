"""
Custom integration to integrate Grocy with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/grocy
"""
import logging
from datetime import timedelta
from typing import Any, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pygrocy import Grocy

from .helpers import extract_base_url_and_path

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

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN] = coordinator

    for platform in PLATFORMS:
        hass.async_add_job(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    await async_setup_services(hass, config_entry)

    # Setup http endpoint for proxying images from grocy
    await async_setup_image_api(hass, config_entry.data)

    return True


class GrocyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, url, api_key, port_number, verify_ssl):
        """Initialize."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        (base_url, path) = extract_base_url_and_path(url)
        self.api = Grocy(
            base_url, api_key, path=path, port=port_number, verify_ssl=verify_ssl
        )
        self.entities = []
        self.data = {}

    async def _async_update_data(self):
        """Update data via library."""
        grocy_data = GrocyData(self.hass, self.api)
        data = {}
        features = await async_supported_features(grocy_data)
        if not features:
            raise UpdateFailed("No features enabled")

        for entity in self.entities:
            if not entity.enabled:
                continue
            if not entity.entity_type in features:
                _LOGGER.debug(
                    "You have enabled the entity for '%s', but this feature is not enabled in Grocy",
                    entity.name,
                )
                continue

            try:
                data[entity.entity_type] = await grocy_data.async_update_data(
                    entity.entity_type
                )
            except Exception as exception:  # pylint: disable=broad-except
                _LOGGER.error(
                    "Update of %s failed with %s",
                    entity.entity_type,
                    exception,
                )
        return data


async def async_supported_features(grocy_data: GrocyData) -> List[str]:
    """Return a list of supported features."""
    features = []
    config = await grocy_data.async_get_config()
    if config:
        if is_enabled_grocy_feature(config, "FEATURE_FLAG_STOCK"):
            features.append(GrocyEntityType.STOCK)
            features.append(GrocyEntityType.PRODUCTS)
            features.append(GrocyEntityType.MISSING_PRODUCTS)
            features.append(GrocyEntityType.EXPIRED_PRODUCTS)
            features.append(GrocyEntityType.EXPIRING_PRODUCTS)

        if is_enabled_grocy_feature(config, "FEATURE_FLAG_SHOPPINGLIST"):
            features.append(GrocyEntityType.SHOPPING_LIST)

        if is_enabled_grocy_feature(config, "FEATURE_FLAG_TASKS"):
            features.append(GrocyEntityType.TASKS)
            features.append(GrocyEntityType.OVERDUE_TASKS)

        if is_enabled_grocy_feature(config, "FEATURE_FLAG_CHORES"):
            features.append(GrocyEntityType.CHORES)
            features.append(GrocyEntityType.OVERDUE_CHORES)

        if is_enabled_grocy_feature(config, "FEATURE_FLAG_RECIPES"):
            features.append(GrocyEntityType.MEAL_PLAN)

    return features


def is_enabled_grocy_feature(grocy_config: Any, feature_setting_key: str) -> bool:
    """
    Return whether the Grocy feature is enabled or not, default is enabled.
    Setting value received from Grocy can be a str or bool.
    """
    feature_setting_value = grocy_config[feature_setting_key]
    return feature_setting_value not in (False, "0")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await async_unload_services(hass)
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        del hass.data[DOMAIN]

    return unloaded
