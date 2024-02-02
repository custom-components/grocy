"""Todo platform for Grocy."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import datetime
import logging
from typing import Any

from pygrocy.data_models.battery import Battery
from pygrocy.data_models.chore import Chore
from pygrocy.data_models.meal_items import MealPlanItem
from pygrocy.data_models.product import Product, ShoppingListProduct
from pygrocy.data_models.task import Task

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_BATTERIES,
    ATTR_CHORES,
    ATTR_MEAL_PLAN,
    ATTR_SHOPPING_LIST,
    ATTR_STOCK,
    ATTR_TASKS,
    DOMAIN,
)
from .coordinator import GrocyCoordinatorData, GrocyDataUpdateCoordinator
from .entity import GrocyEntity
from .helpers import MealPlanItemWrapper
from .services import (
    SERVICE_CHORE_ID,
    SERVICE_DONE_BY,
    SERVICE_ENTITY_TYPE,
    SERVICE_OBJECT_ID,
    SERVICE_SKIPPED,
    SERVICE_TASK_ID,
    async_complete_task_service,
    async_delete_generic_service,
    async_execute_chore_service,
)

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
        key=ATTR_BATTERIES,
        name="Grocy batteries",
        icon="mdi:battery",
        exists_fn=lambda entities: ATTR_BATTERIES in entities,
    ),
    GrocyTodoListEntityDescription(
        key=ATTR_CHORES,
        name="Grocy chores",
        icon="mdi:broom",
        exists_fn=lambda entities: ATTR_CHORES in entities,
    ),
    GrocyTodoListEntityDescription(
        key=ATTR_MEAL_PLAN,
        name="Grocy meal plan",
        icon="mdi:silverware-variant",
        exists_fn=lambda entities: ATTR_MEAL_PLAN in entities,
    ),
    GrocyTodoListEntityDescription(
        key=ATTR_SHOPPING_LIST,
        name="Grocy shopping list",
        icon="mdi:cart-outline",
        exists_fn=lambda entities: ATTR_SHOPPING_LIST in entities,
    ),
    GrocyTodoListEntityDescription(
        key=ATTR_STOCK,
        name="Grocy stock",
        icon="mdi:fridge-outline",
        exists_fn=lambda entities: ATTR_STOCK in entities,
    ),
    GrocyTodoListEntityDescription(
        key=ATTR_TASKS,
        name="Grocy tasks",
        icon="mdi:checkbox-marked-circle-outline",
        exists_fn=lambda entities: ATTR_TASKS in entities,
    ),
)


def _calculate_days_until(
    due: datetime.datetime | datetime.date | None, date_only: bool = False
) -> int:
    return (
        (
            (due.date() if isinstance(due, datetime.datetime) else due)
            - datetime.date.today()
            if date_only
            else due - datetime.datetime.now()
        ).days
        if due
        else 0
    )


def _calculate_item_status(daysUntilDue: int):
    return TodoItemStatus.NEEDS_ACTION if daysUntilDue < 1 else TodoItemStatus.COMPLETED


class GrocyTodoItem(TodoItem):
    def __init__(
        self,
        item: Chore
        | Battery
        | MealPlanItem
        | MealPlanItemWrapper
        | Product
        | ShoppingListProduct
        | Task
        | None = None,
        key: str = "",
    ):
        if isinstance(item, Chore):
            due = item.next_estimated_execution_time
            days_until = _calculate_days_until(due, item.track_date_only)
            super().__init__(
                uid=item.id.__str__(),
                summary=item.name,
                due=due,
                status=_calculate_item_status(days_until),
                description=item.description or None,
            )
        elif isinstance(item, Battery):
            due = item.next_estimated_charge_time
            days_until = _calculate_days_until(due, True)
            super().__init__(
                uid=item.id.__str__(),
                summary=item.name,
                due=due,
                status=_calculate_item_status(days_until),
                description=item.description or None,
            )
        elif isinstance(item, MealPlanItem):
            due = item.day
            days_until = _calculate_days_until(due, True)
            super().__init__(
                uid=item.id.__str__(),
                summary=item.recipe.name,
                due=due,
                status=_calculate_item_status(days_until),
                description=item.recipe.description or None,
            )
        elif isinstance(item, MealPlanItemWrapper):
            due = item.meal_plan.day
            days_until = _calculate_days_until(due, True)
            super().__init__(
                uid=item.meal_plan.id.__str__(),
                summary=item.meal_plan.recipe.name,
                due=due,
                status=_calculate_item_status(days_until),
                description=item.meal_plan.recipe.description or None,
            )
        elif isinstance(item, Product):
            super().__init__(
                uid=item.id.__str__(),
                summary=f"{item.available_amount:.2f}x {item.name}",
                status=TodoItemStatus.NEEDS_ACTION
                if (item.available_amount or 0) > 0
                else TodoItemStatus.COMPLETED,
                # TODO, the description attribute isn't pulled for products in pygrocy
                description=None,
            )
        elif isinstance(item, ShoppingListProduct):
            super().__init__(
                uid=item.id.__str__(),
                summary=f"{item.amount:.2f}x {item.product.name}",
                due=None,
                status=TodoItemStatus.NEEDS_ACTION
                # TODO, needs the 'done' attribute instead; however, this isn't supported by pygrocy yet.
                if item.amount > 0
                else TodoItemStatus.COMPLETED,
                description=item.note or None,
            )
        elif isinstance(item, Task):
            due = item.due_date
            days_until = _calculate_days_until(due, True)
            super().__init__(
                uid=item.id.__str__(),
                summary=item.name,
                due=due,
                status=_calculate_item_status(days_until),
                description=item.description or None,
            )
        else:
            raise NotImplementedError(f"{key} => {type(item)}")


class GrocyTodoListEntity(GrocyEntity, TodoListEntity):
    """Grocy todo entity definition."""

    _attr_supported_features = (
        # TodoListEntityFeature.CREATE_TODO_ITEM
        # TodoListEntityFeature.UPDATE_TODO_ITEM | TodoListEntityFeature.DELETE_TODO_ITEM
        # | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        # | TodoListEntityFeature.SET_DUE_DATETIME_ON_ITEM
        # | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    @property
    def todo_items(self) -> list[TodoItem] | None:
        """Return the value reported by the todo."""
        entity_data = self.coordinator.data[self.entity_description.key]
        return (
            [GrocyTodoItem(item, self.entity_description.key) for item in entity_data]
            if entity_data
            else None
        )

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        raise NotImplementedError()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item in the To-do list."""
        if self.entity_description.key == ATTR_CHORES:
            if item.status == TodoItemStatus.COMPLETED:
                data: dict[str, Any] = {
                    SERVICE_CHORE_ID: item.uid,
                    SERVICE_DONE_BY: 1,
                    SERVICE_SKIPPED: False,
                }
                await async_execute_chore_service(self.hass, self.coordinator, data)
                await self.coordinator.async_refresh()
            else:
                raise NotImplementedError()
        elif self.entity_description.key == ATTR_TASKS:
            if item.status == TodoItemStatus.COMPLETED:
                data: dict[str, Any] = {
                    SERVICE_TASK_ID: item.uid,
                }
                await async_complete_task_service(self.hass, self.coordinator, data)
                await self.coordinator.async_refresh()
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete an item in the To-do list."""
        _LOGGER.warning(uids)
        _LOGGER.warning(self.entity_description.key)
        routines = [
            async_delete_generic_service(
                self.hass,
                self.coordinator,
                {
                    SERVICE_ENTITY_TYPE: self.entity_description.key,
                    SERVICE_OBJECT_ID: int(uid),
                },
            )
            for uid in uids
        ]
        for routine in routines:
            await routine
        await self.coordinator.async_refresh()
