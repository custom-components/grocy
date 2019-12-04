"""Adds config flow for grocy."""
from collections import OrderedDict

import voluptuous as vol
from homeassistant import config_entries
from pygrocy import Grocy

from .const import DEFAULT_PORT_NUMBER, DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class GrocyFlowHandler(config_entries.ConfigFlow):
    """Config flow for grocy."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(
        self, user_input={}
    ):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""
        self._errors = {}
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input["url"], user_input["api_key"],
                user_input["port"],user_input["verify_ssl"]
            )
            if valid:
                return self.async_create_entry(title="Grocy", data=user_input)
            else:
                self._errors["base"] = "auth"
                _LOGGER.error(self._errors)

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""

        # Defaults
        url = ""
        api_key = ""
        port = DEFAULT_PORT_NUMBER
        verify_ssl = True

        if user_input is not None:
            if "url" in user_input:
                url = user_input["url"]
            if "api_key" in user_input:
                api_key = user_input["api_key"]
            if "port" in user_input:
                port = user_input["port"]
            if "verify_ssl" in user_input:
                verify_ssl = user_input["verify_ssl"]

        data_schema = OrderedDict()
        data_schema[vol.Required("url", default=url)] = str
        data_schema[vol.Required("api_key", default=api_key)] = str
        data_schema[vol.Optional("port", default=port)] = int
        data_schema[vol.Optional("verify_ssl", default=verify_ssl)] = bool
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def async_step_import(self, user_input):  # pylint: disable=unused-argument
        """Import a config entry.
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data={})

    async def _test_credentials(self, url, api_key, port, verify_ssl):
        """Return true if credentials is valid."""
        try:
            client = Grocy(url, api_key, port, verify_ssl)
            client.stock()
            return True
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.exception(e)
            pass
        return False
