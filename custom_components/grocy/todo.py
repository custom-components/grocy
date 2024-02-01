"""Todo platform for Grocy."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import datetime
import logging
from typing import Any

from pygrocy.data_models.chore import Chore

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_CHORES, DOMAIN
from .coordinator import GrocyCoordinatorData, GrocyDataUpdateCoordinator
from .entity import GrocyEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Do setup todo platform."""
    coordinator: GrocyDataUpdateCoordinator = hass.data[DOMAIN]
    entities = []
    for description in TODOS:
        if description.exists_fn(coordinator.available_entities):
            entity = GrocyTodoListEntity(coordinator, description, config_entry)
            coordinator.entities.append(entity)
            entities.append(entity)
        else:
            _LOGGER.debug(
                "Entity description '%s' is not available",
                description.key,
            )

    async_add_entities(entities, True)


@dataclass
class GrocyTodoListEntityDescription(EntityDescription):
    """Grocy todo entity description."""

    attributes_fn: Callable[[list[Any]], GrocyCoordinatorData | None] = lambda _: None
    exists_fn: Callable[[list[str]], bool] = lambda _: True
    entity_registry_enabled_default: bool = False


TODOS: tuple[GrocyTodoListEntityDescription, ...] = (
    GrocyTodoListEntityDescription(
        key=ATTR_CHORES,
        name="Grocy chores",
        icon="mdi:broom",
        exists_fn=lambda entities: ATTR_CHORES in entities,
    ),
)


class GrocyTodoItem(TodoItem):
    def __init__(self, chore: Chore):
        due = chore.next_estimated_execution_time
        days_until = (
            due.date() - datetime.date.today()
            if chore.track_date_only
            else due - datetime.datetime.now()
        )
        super().__init__(
            summary=chore.name,
            due=due,
            status=TodoItemStatus.NEEDS_ACTION
            if chore.rollover or days_until.days < 1
            else TodoItemStatus.COMPLETED,
            description=chore.description or None,
        )


class GrocyTodoListEntity(GrocyEntity, TodoListEntity):
    """Grocy todo entity definition."""

    _attr_supported_features = (
        # TodoListEntityFeature.CREATE_TODO_ITEM
        # | TodoListEntityFeature.UPDATE_TODO_ITEM
        # | TodoListEntityFeature.DELETE_TODO_ITEM
        # | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        # | TodoListEntityFeature.SET_DUE_DATETIME_ON_ITEM
        # | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    @property
    def todo_items(self) -> list[TodoItem] | None:
        """Return the value reported by the todo."""
        entity_data = self.coordinator.data[self.entity_description.key]
        return [GrocyTodoItem(item) for item in entity_data] if entity_data else None

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        raise NotImplementedError()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item in the To-do list."""
        raise NotImplementedError()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete an item in the To-do list."""
        raise NotImplementedError()
