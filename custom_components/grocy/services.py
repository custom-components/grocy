"""Grocy services."""
# from pydeconz.utils import normalize_bridge_id
import voluptuous as vol

from homeassistant.helpers import config_validation as cv

# from .config_flow import get_instance
from pygrocy import TransactionType

from .const import (
    #     CONF_BRIDGE_ID,
    DOMAIN,
    #     LOGGER,
    #     NEW_GROUP,
    #     NEW_LIGHT,
    #     NEW_SCENE,
    #     NEW_SENSOR,
)

GROCY_SERVICES = "grocy_services"

SERVICE_PRODUCT_ID = "product_id"
SERVICE_AMOUNT = "amount"
SERVICE_PRICE = "price"
SERVICE_SPOILED = "spoiled"
SERVICE_TRANSACTION_TYPE = "transaction_type"

SERVICE_ADD_PRODUCT = "add_product"
SERVICE_CONSUME_PRODUCT = "consume_product"

SERVICE_ADD_PRODUCT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_PRODUCT_ID): int,
            vol.Required(SERVICE_AMOUNT): int,
            vol.Optional(SERVICE_PRICE): str,
            vol.Optional(SERVICE_PRICE): str,
        }
    )
)

SERVICE_CONSUME_PRODUCT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_PRODUCT_ID): int,
            vol.Required(SERVICE_AMOUNT): int,
            vol.Optional(SERVICE_SPOILED): bool,
            vol.Optional(SERVICE_TRANSACTION_TYPE): TransactionType,
        }
    )
)


async def async_setup_services(hass):
    """Set up services for deCONZ integration."""
    if hass.data.get(GROCY_SERVICES, False):
        return

    hass.data[GROCY_SERVICES] = True

    async def async_call_grocy_service(service_call):
        """Call correct Grocy service."""
        service = service_call.service
        service_data = service_call.data

        if service == SERVICE_ADD_PRODUCT:
            await async_add_product_service(hass, service_data)

        elif service == SERVICE_CONSUME_PRODUCT:
            await async_consume_product_service(hass, service_data)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_PRODUCT,
        async_call_grocy_service,
        schema=SERVICE_ADD_PRODUCT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CONSUME_PRODUCT,
        async_call_grocy_service,
        schema=SERVICE_CONSUME_PRODUCT_SCHEMA,
    )


async def async_unload_services(hass):
    """Unload Grocy services."""
    if not hass.data.get(GROCY_SERVICES):
        return

    hass.data[GROCY_SERVICES] = False

    hass.services.async_remove(DOMAIN, SERVICE_ADD_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_CONSUME_PRODUCT)


async def async_add_product_service(hass, data):
    """Add a product in Grocy."""
    # gateway = get_master_gateway(hass)
    # if CONF_BRIDGE_ID in data:
    #     gateway = hass.data[DOMAIN][normalize_bridge_id(data[CONF_BRIDGE_ID])]

    product_id = data[SERVICE_PRODUCT_ID]
    amount = data[SERVICE_AMOUNT]
    price = data.get(SERVICE_PRICE, "")

    grocy.add_product(product_id, amount, price)


async def async_consume_product_service(hass, data):
    """Consume a product in Grocy."""
    # gateway = get_master_gateway(hass)
    # if CONF_BRIDGE_ID in data:
    #     gateway = hass.data[DOMAIN][normalize_bridge_id(data[CONF_BRIDGE_ID])]

    product_id = data[SERVICE_PRODUCT_ID]
    amount = data[SERVICE_AMOUNT]
    spoiled = data.get("spoiled", False)

    transaction_type_raw = data.get(SERVICE_TRANSACTION_TYPE, None)
    transaction_type = TransactionType.CONSUME

    if transaction_type_raw is not None:
        transaction_type = TransactionType[transaction_type_raw]
    grocy.consume_product(
        product_id, amount, spoiled=spoiled, transaction_type=transaction_type
    )
