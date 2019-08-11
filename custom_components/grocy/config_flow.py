"""Adds config flow for grocy."""
from collections import OrderedDict
import voluptuous as vol
from pygrocy import Grocy
from homeassistant import config_entries

from .const import DOMAIN


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
                user_input["url"], user_input["api_key"]
            )
            if valid:
                return self.async_create_entry(title="Grocy", data=user_input)
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""

        # Defaults
        url = ""
        api_key = ""

        if user_input is not None:
            if "url" in user_input:
                url = user_input["url"]
            if "api_key" in user_input:
                api_key = user_input["api_key"]

        data_schema = OrderedDict()
        data_schema[vol.Required("url", default=url)] = str
        data_schema[vol.Required("api_key", default=api_key)] = str
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

    async def _test_credentials(self, url, api_key):
        """Return true if credentials is valid."""
        try:
            client = Grocy(url, api_key)
            client.stock()
            return True
        except Exception:  # pylint: disable=broad-except
            pass
        return False