"""Todo platform for Grocy."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import datetime
import logging
from typing import Any

from pygrocy.data_models.chore import Chore

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    ATTR_BATTERIES,
    ATTR_CHORES,
    ATTR_MEAL_PLAN,
    ATTR_SHOPPING_LIST,
    ATTR_STOCK,
    ATTR_TASKS,
    CHORES,
    DOMAIN,
    ITEMS,
    MEAL_PLANS,
    PRODUCTS,
    TASKS,
)
from .coordinator import GrocyDataUpdateCoordinator
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
class GrocyTodoListEntityDescription:
    """Grocy todo entity description."""

    key: str = None
    name: str = None
    icon: str = None
    summary: str = None
    status: str = None
    due: any = None
    description: str = None
    items: Mapping[str, any]
    attributes_fn: Callable[[list[Any]], Mapping[str, Any] | None] = lambda _: None
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
            due - datetime.date.today()
            if chore.track_date_only
            else due - datetime.datetime.now()
        )
        super().__init__(
            summary=chore.name,
            due=due,
            status=TodoItemStatus.COMPLETED
            if chore.rollover or days_until < 1
            else TodoItemStatus.NEEDS_ACTION,
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

    def __init__(  # noqa: D107
        self,
        coordinator: GrocyDataUpdateCoordinator,
        description: GrocyTodoListEntityDescription,
        config_entry: ConfigEntry,
    ) -> None:
        data: list[Chore] = self.coordinator.data.get(self.entity_description.key)
        self._attr_todo_items = [GrocyTodoItem(item) for item in data]
        super().__init__(coordinator, description, config_entry)

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the todo."""
        entity_data = self.coordinator.data.get(self.entity_description.key, None)

        return len(entity_data) if entity_data else 0

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        raise NotImplementedError()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item in the To-do list."""
        raise NotImplementedError()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete an item in the To-do list."""
        raise NotImplementedError()
