"""Adds config flow for Grocy."""
from homeassistant import config_entries
from homeassistant.core import callback
from pygrocy import Grocy
import voluptuous as vol
from collections import OrderedDict
import logging

from .const import (  # pylint: disable=unused-import
    NAME,
    DOMAIN,
    PLATFORMS,
    DEFAULT_PORT,
    CONF_URL,
    CONF_PORT,
    CONF_API_KEY,
    CONF_VERIFY_SSL,
    CONF_ALLOW_CHORES,
    CONF_ALLOW_MEAL_PLAN,
    CONF_ALLOW_PRODUCTS,
    CONF_ALLOW_SHOPPING_LIST,
    CONF_ALLOW_STOCK,
    CONF_ALLOW_TASKS,
    DEFAULT_CONF_PORT_NUMBER,
    DEFAULT_CONF_ALLOW_CHORES,
    DEFAULT_CONF_ALLOW_MEAL_PLAN,
    DEFAULT_CONF_ALLOW_SHOPPING_LIST,
    DEFAULT_CONF_ALLOW_STOCK,
    DEFAULT_CONF_ALLOW_TASKS,
)

_LOGGER = logging.getLogger(__name__)


class GrocyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(
        self, user_input=None  # pylint: disable=bad-continuation
    ):
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GrocyOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit the data."""
        data_schema = OrderedDict()
        # TODO remove
        data_schema[vol.Required(CONF_URL, default="http://192.168.1.78")] = str
        # TODO remove
        data_schema[
            vol.Required(
                CONF_API_KEY,
                default="uZlwmnzzCnF1hpvNHNXbcCG0tmFB06h12bMZC4ggLxGja5Yg9X",
            )
        ] = str
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


class GrocyOptionsFlowHandler(config_entries.OptionsFlow):
    """Grocy config flow options handler."""

    def __init__(self, config_entry):
        """Initialize Grocy options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ALLOW_CHORES,
                        default=self.config_entry.options.get(
                            CONF_ALLOW_CHORES, DEFAULT_CONF_ALLOW_CHORES
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_ALLOW_MEAL_PLAN,
                        default=self.config_entry.options.get(
                            CONF_ALLOW_MEAL_PLAN, DEFAULT_CONF_ALLOW_MEAL_PLAN
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_ALLOW_SHOPPING_LIST,
                        default=self.config_entry.options.get(
                            CONF_ALLOW_SHOPPING_LIST, DEFAULT_CONF_ALLOW_SHOPPING_LIST
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_ALLOW_STOCK,
                        default=self.config_entry.options.get(
                            CONF_ALLOW_STOCK, DEFAULT_CONF_ALLOW_STOCK
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_ALLOW_TASKS,
                        default=self.config_entry.options.get(
                            CONF_ALLOW_TASKS, DEFAULT_CONF_ALLOW_TASKS
                        ),
                    ): bool,
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(NAME), data=self.options
        )
