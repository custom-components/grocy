"""Grocy services."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from pygrocy import EntityType, TransactionType

from .const import ATTR_CHORES, ATTR_TASKS, DOMAIN
from .coordinator import GrocyDataUpdateCoordinator

SERVICE_PRODUCT_ID = "product_id"
SERVICE_AMOUNT = "amount"
SERVICE_PRICE = "price"
SERVICE_SPOILED = "spoiled"
SERVICE_SUBPRODUCT_SUBSTITUTION = "allow_subproduct_substitution"
SERVICE_TRANSACTION_TYPE = "transaction_type"
SERVICE_CHORE_ID = "chore_id"
SERVICE_DONE_BY = "done_by"
SERVICE_SKIPPED = "skipped"
SERVICE_TASK_ID = "task_id"
SERVICE_ENTITY_TYPE = "entity_type"
SERVICE_DATA = "data"
SERVICE_RECIPE_ID = "recipe_id"
SERVICE_BATTERY_ID = "battery_id"
SERVICE_OBJECT_ID = "object_id"

SERVICE_ADD_PRODUCT = "add_product_to_stock"
SERVICE_OPEN_PRODUCT = "open_product"
SERVICE_CONSUME_PRODUCT = "consume_product_from_stock"
SERVICE_EXECUTE_CHORE = "execute_chore"
SERVICE_COMPLETE_TASK = "complete_task"
SERVICE_ADD_GENERIC = "add_generic"
SERVICE_UPDATE_GENERIC = "update_generic"
SERVICE_DELETE_GENERIC = "delete_generic"
SERVICE_CONSUME_RECIPE = "consume_recipe"
SERVICE_TRACK_BATTERY = "track_battery"

SERVICE_ADD_PRODUCT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_PRODUCT_ID): vol.Coerce(int),
            vol.Required(SERVICE_AMOUNT): vol.Coerce(float),
            vol.Optional(SERVICE_PRICE): str,
        }
    )
)

SERVICE_OPEN_PRODUCT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_PRODUCT_ID): vol.Coerce(int),
            vol.Required(SERVICE_AMOUNT): vol.Coerce(float),
            vol.Optional(SERVICE_SUBPRODUCT_SUBSTITUTION): bool,
        }
    )
)

SERVICE_CONSUME_PRODUCT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_PRODUCT_ID): vol.Coerce(int),
            vol.Required(SERVICE_AMOUNT): vol.Coerce(float),
            vol.Optional(SERVICE_SPOILED): bool,
            vol.Optional(SERVICE_SUBPRODUCT_SUBSTITUTION): bool,
            vol.Optional(SERVICE_TRANSACTION_TYPE): str,
        }
    )
)

SERVICE_EXECUTE_CHORE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_CHORE_ID): vol.Coerce(int),
            vol.Optional(SERVICE_DONE_BY): vol.Coerce(int),
            vol.Optional(SERVICE_SKIPPED): bool,
        }
    )
)

SERVICE_COMPLETE_TASK_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_TASK_ID): vol.Coerce(int),
        }
    )
)

SERVICE_ADD_GENERIC_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_ENTITY_TYPE): str,
            vol.Required(SERVICE_DATA): object,
        }
    )
)

SERVICE_UPDATE_GENERIC_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_ENTITY_TYPE): str,
            vol.Required(SERVICE_OBJECT_ID): vol.Coerce(int),
            vol.Required(SERVICE_DATA): object,
        }
    )
)

SERVICE_DELETE_GENERIC_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_ENTITY_TYPE): str,
            vol.Required(SERVICE_OBJECT_ID): vol.Coerce(int),
        }
    )
)

SERVICE_CONSUME_RECIPE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_RECIPE_ID): vol.Coerce(int),
        }
    )
)

SERVICE_TRACK_BATTERY_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_BATTERY_ID): vol.Coerce(int),
        }
    )
)

SERVICES_WITH_ACCOMPANYING_SCHEMA: list[tuple[str, vol.Schema]] = [
    (SERVICE_ADD_PRODUCT, SERVICE_ADD_PRODUCT_SCHEMA),
    (SERVICE_OPEN_PRODUCT, SERVICE_OPEN_PRODUCT_SCHEMA),
    (SERVICE_CONSUME_PRODUCT, SERVICE_CONSUME_PRODUCT_SCHEMA),
    (SERVICE_EXECUTE_CHORE, SERVICE_EXECUTE_CHORE_SCHEMA),
    (SERVICE_COMPLETE_TASK, SERVICE_COMPLETE_TASK_SCHEMA),
    (SERVICE_ADD_GENERIC, SERVICE_ADD_GENERIC_SCHEMA),
    (SERVICE_UPDATE_GENERIC, SERVICE_UPDATE_GENERIC_SCHEMA),
    (SERVICE_DELETE_GENERIC, SERVICE_DELETE_GENERIC_SCHEMA),
    (SERVICE_CONSUME_RECIPE, SERVICE_CONSUME_RECIPE_SCHEMA),
    (SERVICE_TRACK_BATTERY, SERVICE_TRACK_BATTERY_SCHEMA),
]


async def async_setup_services(
    hass: HomeAssistant, config_entry: ConfigEntry  # pylint: disable=unused-argument
) -> None:
    """Set up services for Grocy integration."""
    coordinator: GrocyDataUpdateCoordinator = hass.data[DOMAIN]
    if hass.services.async_services().get(DOMAIN):
        return

    async def async_call_grocy_service(service_call: ServiceCall) -> None:
        """Call correct Grocy service."""
        service = service_call.service
        service_data = service_call.data

        if service == SERVICE_ADD_PRODUCT:
            await async_add_product_service(hass, coordinator, service_data)

        elif service == SERVICE_OPEN_PRODUCT:
            await async_open_product_service(hass, coordinator, service_data)

        elif service == SERVICE_CONSUME_PRODUCT:
            await async_consume_product_service(hass, coordinator, service_data)

        elif service == SERVICE_EXECUTE_CHORE:
            await async_execute_chore_service(hass, coordinator, service_data)

        elif service == SERVICE_COMPLETE_TASK:
            await async_complete_task_service(hass, coordinator, service_data)

        elif service == SERVICE_ADD_GENERIC:
            await async_add_generic_service(hass, coordinator, service_data)

        elif service == SERVICE_UPDATE_GENERIC:
            await async_update_generic_service(hass, coordinator, service_data)

        elif service == SERVICE_DELETE_GENERIC:
            await async_delete_generic_service(hass, coordinator, service_data)

        elif service == SERVICE_CONSUME_RECIPE:
            await async_consume_recipe_service(hass, coordinator, service_data)

        elif service == SERVICE_TRACK_BATTERY:
            await async_track_battery_service(hass, coordinator, service_data)

    for service, schema in SERVICES_WITH_ACCOMPANYING_SCHEMA:
        hass.services.async_register(DOMAIN, service, async_call_grocy_service, schema)


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Grocy services."""
    if not hass.services.async_services().get(DOMAIN):
        return

    for service, _ in SERVICES_WITH_ACCOMPANYING_SCHEMA:
        hass.services.async_remove(DOMAIN, service)


async def async_add_product_service(hass, coordinator, data):
    """Add a product in Grocy."""
    product_id = data[SERVICE_PRODUCT_ID]
    amount = data[SERVICE_AMOUNT]
    price = data.get(SERVICE_PRICE, "")

    def wrapper():
        coordinator.grocy_api.add_product(product_id, amount, price)

    await hass.async_add_executor_job(wrapper)


async def async_open_product_service(hass, coordinator, data):
    """Open a product in Grocy."""
    product_id = data[SERVICE_PRODUCT_ID]
    amount = data[SERVICE_AMOUNT]
    allow_subproduct_substitution = data.get(SERVICE_SUBPRODUCT_SUBSTITUTION, False)

    def wrapper():
        coordinator.grocy_api.open_product(
            product_id, amount, allow_subproduct_substitution
        )

    await hass.async_add_executor_job(wrapper)


async def async_consume_product_service(hass, coordinator, data):
    """Consume a product in Grocy."""
    product_id = data[SERVICE_PRODUCT_ID]
    amount = data[SERVICE_AMOUNT]
    spoiled = data.get(SERVICE_SPOILED, False)
    allow_subproduct_substitution = data.get(SERVICE_SUBPRODUCT_SUBSTITUTION, False)

    transaction_type_raw = data.get(SERVICE_TRANSACTION_TYPE, None)
    transaction_type = TransactionType.CONSUME

    if transaction_type_raw is not None:
        transaction_type = TransactionType[transaction_type_raw]

    def wrapper():
        coordinator.grocy_api.consume_product(
            product_id,
            amount,
            spoiled=spoiled,
            transaction_type=transaction_type,
            allow_subproduct_substitution=allow_subproduct_substitution,
        )

    await hass.async_add_executor_job(wrapper)


async def async_execute_chore_service(hass, coordinator, data):
    """Execute a chore in Grocy."""
    chore_id = data[SERVICE_CHORE_ID]
    done_by = data.get(SERVICE_DONE_BY, "")
    skipped = data.get(SERVICE_SKIPPED, False)

    def wrapper():
        coordinator.grocy_api.execute_chore(chore_id, done_by, skipped=skipped)

    await hass.async_add_executor_job(wrapper)
    await _async_force_update_entity(coordinator, ATTR_CHORES)


async def async_complete_task_service(hass, coordinator, data):
    """Complete a task in Grocy."""
    task_id = data[SERVICE_TASK_ID]

    def wrapper():
        coordinator.grocy_api.complete_task(task_id)

    await hass.async_add_executor_job(wrapper)
    await _async_force_update_entity(coordinator, ATTR_TASKS)


async def async_add_generic_service(hass, coordinator, data):
    """Add a generic entity in Grocy."""
    entity_type_raw = data.get(SERVICE_ENTITY_TYPE, None)
    entity_type = EntityType.TASKS

    if entity_type_raw is not None:
        entity_type = EntityType(entity_type_raw)

    data = data[SERVICE_DATA]

    def wrapper():
        coordinator.grocy_api.add_generic(entity_type, data)

    await hass.async_add_executor_job(wrapper)
    await post_generic_refresh(coordinator, entity_type);


async def async_update_generic_service(hass, coordinator, data):
    """Update a generic entity in Grocy."""
    entity_type_raw = data.get(SERVICE_ENTITY_TYPE, None)
    entity_type = EntityType.TASKS

    if entity_type_raw is not None:
        entity_type = EntityType(entity_type_raw)

    object_id = data[SERVICE_OBJECT_ID]

    data = data[SERVICE_DATA]

    def wrapper():
        coordinator.grocy_api.update_generic(entity_type, object_id, data)

    await hass.async_add_executor_job(wrapper)
    await post_generic_refresh(coordinator, entity_type);


async def async_delete_generic_service(hass, coordinator, data):
    """Delete a generic entity in Grocy."""
    entity_type_raw = data.get(SERVICE_ENTITY_TYPE, None)
    entity_type = EntityType.TASKS

    if entity_type_raw is not None:
        entity_type = EntityType(entity_type_raw)

    object_id = data[SERVICE_OBJECT_ID]

    def wrapper():
        coordinator.grocy_api.delete_generic(entity_type, object_id)

    await hass.async_add_executor_job(wrapper)
    await post_generic_refresh(coordinator, entity_type);


async def post_generic_refresh(coordinator, entity_type):
    if entity_type == "tasks" or entity_type == "chores":
        await _async_force_update_entity(coordinator, entity_type)

async def async_consume_recipe_service(hass, coordinator, data):
    """Consume a recipe in Grocy."""
    recipe_id = data[SERVICE_RECIPE_ID]

    def wrapper():
        coordinator.grocy_api.consume_recipe(recipe_id)

    await hass.async_add_executor_job(wrapper)


async def async_track_battery_service(hass, coordinator, data):
    """Track a battery in Grocy."""
    battery_id = data[SERVICE_BATTERY_ID]

    def wrapper():
        coordinator.grocy_api.charge_battery(battery_id)

    await hass.async_add_executor_job(wrapper)


async def _async_force_update_entity(
    coordinator: GrocyDataUpdateCoordinator, entity_key: str
) -> None:
    """Force entity update for given entity key."""
    entity = next(
        (
            entity
            for entity in coordinator.entities
            if entity.entity_description.key == entity_key
        ),
        None,
    )
    if entity:
        await entity.async_update_ha_state(force_refresh=True)
