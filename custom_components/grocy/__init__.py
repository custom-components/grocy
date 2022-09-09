"""
Custom integration to integrate Grocy with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/grocy
"""
from __future__ import annotations

import logging
from typing import List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pygrocy import Grocy

from .const import (
    ATTR_BATTERIES,
    ATTR_CHORES,
    ATTR_EXPIRED_PRODUCTS,
    ATTR_EXPIRING_PRODUCTS,
    ATTR_MEAL_PLAN,
    ATTR_MISSING_PRODUCTS,
    ATTR_OVERDUE_BATTERIES,
    ATTR_OVERDUE_CHORES,
    ATTR_OVERDUE_PRODUCTS,
    ATTR_OVERDUE_TASKS,
    ATTR_SHOPPING_LIST,
    ATTR_STOCK,
    ATTR_TASKS,
    CONF_API_KEY,
    CONF_PORT,
    CONF_URL,
    CONF_VERIFY_SSL,
    DOMAIN,
    GROCY_AVAILABLE_ENTITIES,
    GROCY_CLIENT,
    PLATFORMS,
    REGISTERED_ENTITIES,
    STARTUP_MESSAGE,
)
from .grocy_data import GrocyData, async_setup_endpoint_for_image_proxy
from .helpers import extract_base_url_and_path
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    _LOGGER.info(STARTUP_MESSAGE)

    grocy_client = setup_grocy_client(hass, config_entry)
    available_entities = await _async_get_available_entities(grocy_client)

    hass.data.setdefault(
        DOMAIN,
        {
            GROCY_CLIENT: grocy_client,
            GROCY_AVAILABLE_ENTITIES: available_entities,
            REGISTERED_ENTITIES: [],
        },
    )

    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)
    await async_setup_services(hass, config_entry)
    await async_setup_endpoint_for_image_proxy(hass, config_entry.data)

    return True


def setup_grocy_client(hass: HomeAssistant, config_entry: ConfigEntry) -> GrocyData:
    """Initialize Grocy"""
    url = config_entry.data[CONF_URL]
    api_key = config_entry.data[CONF_API_KEY]
    port = config_entry.data[CONF_PORT]
    verify_ssl = config_entry.data[CONF_VERIFY_SSL]

    (base_url, path) = extract_base_url_and_path(url)

    grocy_api = Grocy(base_url, api_key, path=path, port=port, verify_ssl=verify_ssl)
    return GrocyData(hass, grocy_api)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await async_unload_services(hass)
    if unloaded := await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    ):
        del hass.data[DOMAIN]

    return unloaded


async def _async_get_available_entities(grocy_client: GrocyData) -> List[str]:
    """Return a list of available entities based on enabled Grocy features."""
    available_entities = []
    grocy_config = await grocy_client.async_get_config()
    if grocy_config:
        if "FEATURE_FLAG_STOCK" in grocy_config.enabled_features:
            available_entities.append(ATTR_STOCK)
            available_entities.append(ATTR_MISSING_PRODUCTS)
            available_entities.append(ATTR_EXPIRED_PRODUCTS)
            available_entities.append(ATTR_EXPIRING_PRODUCTS)
            available_entities.append(ATTR_OVERDUE_PRODUCTS)

        if "FEATURE_FLAG_SHOPPINGLIST" in grocy_config.enabled_features:
            available_entities.append(ATTR_SHOPPING_LIST)

        if "FEATURE_FLAG_TASKS" in grocy_config.enabled_features:
            available_entities.append(ATTR_TASKS)
            available_entities.append(ATTR_OVERDUE_TASKS)

        if "FEATURE_FLAG_CHORES" in grocy_config.enabled_features:
            available_entities.append(ATTR_CHORES)
            available_entities.append(ATTR_OVERDUE_CHORES)

        if "FEATURE_FLAG_RECIPES" in grocy_config.enabled_features:
            available_entities.append(ATTR_MEAL_PLAN)

        if "FEATURE_FLAG_BATTERIES" in grocy_config.enabled_features:
            available_entities.append(ATTR_BATTERIES)
            available_entities.append(ATTR_OVERDUE_BATTERIES)

    _LOGGER.debug("Available entities: %s", available_entities)

    return available_entities
