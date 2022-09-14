"""Grocy services."""
from __future__ import annotations

from typing import List

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity import Entity
from pygrocy import EntityType, TransactionType

from .const import (
    ATTR_CHORES,
    ATTR_TASKS,
    DOMAIN,
    GROCY_CLIENT,
    REGISTERED_ENTITIES,
    SERVICE_ADD_GENERIC,
    SERVICE_ADD_PRODUCT,
    SERVICE_AMOUNT,
    SERVICE_BATTERY_ID,
    SERVICE_CHORE_ID,
    SERVICE_COMPLETE_TASK,
    SERVICE_CONSUME_PRODUCT,
    SERVICE_CONSUME_RECIPE,
    SERVICE_DATA,
    SERVICE_DONE_BY,
    SERVICE_ENTITY_TYPE,
    SERVICE_EXECUTE_CHORE,
    SERVICE_OPEN_PRODUCT,
    SERVICE_PRICE,
    SERVICE_PRODUCT_ID,
    SERVICE_RECIPE_ID,
    SERVICE_SKIPPED,
    SERVICE_SPOILED,
    SERVICE_SUBPRODUCT_SUBSTITUTION,
    SERVICE_TASK_ID,
    SERVICE_TRACK_BATTERY,
    SERVICE_TRANSACTION_TYPE,
)
from .grocy_data import GrocyData

SERVICE_ADD_PRODUCT_SCHEMA = {
    vol.Required(SERVICE_PRODUCT_ID): vol.Coerce(int),
    vol.Required(SERVICE_AMOUNT): vol.Coerce(float),
    vol.Optional(SERVICE_PRICE): str,
}

SERVICE_CONSUME_PRODUCT_SCHEMA = {
    vol.Required(SERVICE_PRODUCT_ID): vol.Coerce(int),
    vol.Required(SERVICE_AMOUNT): vol.Coerce(float),
    vol.Optional(SERVICE_SPOILED): bool,
    vol.Optional(SERVICE_SUBPRODUCT_SUBSTITUTION): bool,
    vol.Optional(SERVICE_TRANSACTION_TYPE): str,
}

SERVICE_OPEN_PRODUCT_SCHEMA = {
    vol.Required(SERVICE_PRODUCT_ID): vol.Coerce(int),
    vol.Required(SERVICE_AMOUNT): vol.Coerce(float),
    vol.Optional(SERVICE_SUBPRODUCT_SUBSTITUTION): bool,
}

SERVICE_EXECUTE_CHORE_SCHEMA = {
    vol.Required(SERVICE_CHORE_ID): vol.Coerce(int),
    vol.Optional(SERVICE_DONE_BY): vol.Coerce(int),
    vol.Optional(SERVICE_SKIPPED): bool,
}

SERVICE_COMPLETE_TASK_SCHEMA = {
    vol.Required(SERVICE_TASK_ID): vol.Coerce(int),
}

SERVICE_ADD_GENERIC_SCHEMA = {
    vol.Required(SERVICE_ENTITY_TYPE): str,
    vol.Required(SERVICE_DATA): object,
}

SERVICE_CONSUME_RECIPE_SCHEMA = {
    vol.Required(SERVICE_RECIPE_ID): vol.Coerce(int),
}

SERVICE_TRACK_BATTERY_SCHEMA = {
    vol.Required(SERVICE_BATTERY_ID): vol.Coerce(int),
}


def make_service_schema(schema: dict):
    """Create a service schema."""
    return vol.Schema(
        vol.All(
            vol.Schema(
                {
                    **schema,
                },
            ),
        )
    )


async def async_setup_services(
    hass: HomeAssistant, config_entry: ConfigEntry  # pylint: disable=unused-argument
) -> None:
    """Set up services for Grocy integration."""
    if hass.services.async_services().get(DOMAIN):
        return

    grocy_client: GrocyData = hass.data[DOMAIN][GROCY_CLIENT]

    async def _async_add_product(call: ServiceCall) -> None:
        """Add a product service call handler."""
        product_id = call.data[SERVICE_PRODUCT_ID]
        amount = call.data[SERVICE_AMOUNT]
        price = call.data.get(SERVICE_PRICE, "")

        await grocy_client.async_add_product(product_id, amount, price)

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_ADD_PRODUCT,
        schema=make_service_schema(SERVICE_ADD_PRODUCT_SCHEMA),
        service_func=_async_add_product,
    )

    async def _async_consume_product(call: ServiceCall) -> None:
        """Consume a product service call handler."""
        product_id = call.data[SERVICE_PRODUCT_ID]
        amount = call.data[SERVICE_AMOUNT]
        spoiled = call.data.get(SERVICE_SPOILED, False)
        allow_subproduct_substitution = call.data.get(
            SERVICE_SUBPRODUCT_SUBSTITUTION, False
        )

        transaction_type_raw = call.data.get(SERVICE_TRANSACTION_TYPE, None)
        transaction_type = TransactionType.CONSUME

        if transaction_type_raw is not None:
            transaction_type = TransactionType[transaction_type_raw]

        await grocy_client.async_consume_product(
            product_id, amount, spoiled, transaction_type, allow_subproduct_substitution
        )

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_CONSUME_PRODUCT,
        schema=make_service_schema(SERVICE_CONSUME_PRODUCT_SCHEMA),
        service_func=_async_consume_product,
    )

    async def _async_open_product(call: ServiceCall) -> None:
        """Open a product service call handler."""
        product_id = call.data[SERVICE_PRODUCT_ID]
        amount = call.data[SERVICE_AMOUNT]
        allow_subproduct_substitution = call.data.get(
            SERVICE_SUBPRODUCT_SUBSTITUTION, False
        )

        await grocy_client.async_open_product(
            product_id, amount, allow_subproduct_substitution
        )

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_OPEN_PRODUCT,
        schema=make_service_schema(SERVICE_OPEN_PRODUCT_SCHEMA),
        service_func=_async_open_product,
    )

    async def _async_execute_chore(call: ServiceCall) -> None:
        """Execute a chore service call handler."""
        chore_id = call.data[SERVICE_CHORE_ID]
        done_by = call.data.get(SERVICE_DONE_BY, "")
        skipped = call.data.get(SERVICE_SKIPPED, False)

        await grocy_client.async_execute_chore(chore_id, done_by, skipped)
        await _async_force_update_entity(
            hass.data[DOMAIN][REGISTERED_ENTITIES], ATTR_CHORES
        )

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_EXECUTE_CHORE,
        schema=make_service_schema(SERVICE_EXECUTE_CHORE_SCHEMA),
        service_func=_async_execute_chore,
    )

    async def _async_complete_task(call: ServiceCall) -> None:
        """Complete a task service call handler."""
        task_id = call.data[SERVICE_TASK_ID]

        await grocy_client.async_complete_task(task_id)
        await _async_force_update_entity(
            hass.data[DOMAIN][REGISTERED_ENTITIES], ATTR_TASKS
        )

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_COMPLETE_TASK,
        schema=make_service_schema(SERVICE_COMPLETE_TASK_SCHEMA),
        service_func=_async_complete_task,
    )

    async def _async_consume_recipe(call: ServiceCall) -> None:
        """Consume a recipe service call handler."""
        recipe_id = call.data[SERVICE_RECIPE_ID]

        await grocy_client.async_consume_recipe(recipe_id)

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_CONSUME_RECIPE,
        schema=make_service_schema(SERVICE_CONSUME_RECIPE_SCHEMA),
        service_func=_async_consume_recipe,
    )

    async def _async_track_battery(call: ServiceCall) -> None:
        """Track a battery service call handler."""
        battery_id = call.data[SERVICE_BATTERY_ID]

        await grocy_client.async_track_battery(battery_id)

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_TRACK_BATTERY,
        schema=make_service_schema(SERVICE_TRACK_BATTERY_SCHEMA),
        service_func=_async_track_battery,
    )

    async def _async_add_generic(call: ServiceCall) -> None:
        """Add a generic entity service call handler."""
        entity_type_raw = call.data.get(SERVICE_ENTITY_TYPE, None)
        entity_type = EntityType.TASKS
        if entity_type_raw is not None:
            entity_type = EntityType(entity_type_raw)
        data = call.data[SERVICE_DATA]

        await grocy_client.async_add_generic(entity_type, data)

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_ADD_GENERIC,
        schema=make_service_schema(SERVICE_ADD_GENERIC_SCHEMA),
        service_func=_async_add_generic,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Grocy services."""
    for service in hass.services.async_services().get(DOMAIN):
        hass.services.async_remove(DOMAIN, service)


async def _async_force_update_entity(entities: List[Entity], entity_key: str) -> None:
    """Force entity update for given entity key."""
    entity = next(
        (entity for entity in entities if entity.entity_description.key == entity_key),
        None,
    )
    if entity:
        await entity.async_update_ha_state(force_refresh=True)
