"""Adds config flow for Grocy."""
import logging
from collections import OrderedDict

import voluptuous as vol
from homeassistant import config_entries
from pygrocy import Grocy

from .const import (
    CONF_API_KEY,
    CONF_PORT,  # pylint: disable=unused-import
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_PORT,
    DOMAIN,
    NAME,
)

_LOGGER = logging.getLogger(__name__)


class GrocyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Grocy."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        _LOGGER.debug("Step user")

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_URL],
                user_input[CONF_API_KEY],
                user_input[CONF_PORT],
                user_input[CONF_VERIFY_SSL],
            )
            _LOGGER.debug("Testing of credentials returned: ")
            _LOGGER.debug(valid)
            if valid:
                return self.async_create_entry(title=NAME, data=user_input)
            else:
                self._errors["base"] = "auth"
            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit the data."""
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_URL, default="")] = str
        data_schema[vol.Required(CONF_API_KEY, default="",)] = str
        data_schema[vol.Optional(CONF_PORT, default=DEFAULT_PORT)] = int
        data_schema[vol.Optional(CONF_VERIFY_SSL, default=False)] = bool
        _LOGGER.debug("config form")

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors,
        )

    async def _test_credentials(self, url, api_key, port, verify_ssl):
        """Return true if credentials is valid."""
        try:
            client = Grocy(url, api_key, port, verify_ssl)

            _LOGGER.debug("Testing credentials")

            def system_info():
                """Get system information from Grocy."""
                client._api_client._do_get_request("/api/system/info")

            await self.hass.async_add_executor_job(system_info)
            return True
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.error(e)
            pass
        return False
