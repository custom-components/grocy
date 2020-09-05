"""
Custom integration to integrate Grocy with Home Assistant.

For more details about this integration, please refer to
https://github.com/custom-components/grocy
"""
import asyncio
from datetime import timedelta
import os
import logging
import hashlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pygrocy import Grocy

from .const import (
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
    CONF_URL,
    CONF_API_KEY,
    CONF_PORT,
    CONF_VERIFY_SSL,
    REQUIRED_FILES,
)
from .grocy_data import GrocyData, async_setup_image_api
from .services import async_setup_services

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    if not await hass.async_add_executor_job(check_files, hass):
        return False

    url = config_entry.data.get(CONF_URL)
    api_key = config_entry.data.get(CONF_API_KEY)
    port_number = config_entry.data.get(CONF_PORT)
    verify_ssl = config_entry.data.get(CONF_VERIFY_SSL)

    coordinator = GrocyDataUpdateCoordinator(
        hass, url, api_key, port_number, verify_ssl
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    for platform in PLATFORMS:
        hass.async_add_job(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    await async_setup_services(hass, config_entry)

    # Setup http endpoint for proxying images from grocy
    await async_setup_image_api(hass, config_entry.data)

    config_entry.add_update_listener(async_reload_entry)
    return True


def check_files(hass):
    """Verify that the user downloaded all files."""

    base = "{}/custom_components/{}/".format(hass.config.path(), DOMAIN)
    missing = []
    for file in REQUIRED_FILES:
        fullpath = "{}{}".format(base, file)
        if not os.path.exists(fullpath):
            missing.append(file)

    if missing:
        _LOGGER.critical("The following files are missing: %s", str(missing))
        returnvalue = False
    else:
        returnvalue = True

    return returnvalue


class GrocyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, url, api_key, port_number, verify_ssl):
        """Initialize."""
        self.api = Grocy(url, api_key, port_number, verify_ssl)
        self.platforms = []
        self.hass = hass
        hash_key = hashlib.md5(
            api_key.encode("utf-8") + url.encode("utf-8")
        ).hexdigest()
        self.hash_key = hash_key
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            grocy_data = GrocyData(self.hass, self.api)
            for platform in self.platforms:
                data = await grocy_data.async_update_data(platform)
                _LOGGER.debug(data)
            return ""
        except Exception as exception:
            raise UpdateFailed(exception)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    _LOGGER.debug("Unloading with state %s", entry.state)
    if entry.state == "loaded":
        try:
            unloaded = all(
                await asyncio.gather(
                    *[
                        hass.config_entries.async_forward_entry_unload(entry, platform)
                        for platform in PLATFORMS
                    ]
                )
            )
            _LOGGER.debug("Unloaded? %s", unloaded)
            return unloaded

        except ValueError:
            pass


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
