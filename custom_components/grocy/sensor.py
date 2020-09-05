"""Sensor platform for Grocy."""

import logging

# pylint: disable=relative-beyond-top-level
from .const import (
    DEFAULT_NAME,
    DOMAIN,
    ICON,
    SENSOR,
    SENSOR_TYPES,
    CHORES_NAME,
    MEAL_PLAN_NAME,
    SHOPPING_LIST_NAME,
    STOCK_NAME,
    TASKS_NAME,
    CONF_ALLOW_CHORES,
    CONF_ALLOW_MEAL_PLAN,
    CONF_ALLOW_SHOPPING_LIST,
    CONF_ALLOW_STOCK,
    CONF_ALLOW_TASKS,
    DEFAULT_CONF_ALLOW_CHORES,
    DEFAULT_CONF_ALLOW_MEAL_PLAN,
    DEFAULT_CONF_ALLOW_SHOPPING_LIST,
    DEFAULT_CONF_ALLOW_STOCK,
    DEFAULT_CONF_ALLOW_TASKS,
)
from .entity import GrocyEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    options_allow_chores = entry.options.get(
        CONF_ALLOW_CHORES, DEFAULT_CONF_ALLOW_CHORES
    )
    options_allow_meal_plan = entry.options.get(
        CONF_ALLOW_MEAL_PLAN, DEFAULT_CONF_ALLOW_MEAL_PLAN
    )
    options_allow_shopping_list = entry.options.get(
        CONF_ALLOW_SHOPPING_LIST, DEFAULT_CONF_ALLOW_SHOPPING_LIST
    )
    options_allow_stock = entry.options.get(CONF_ALLOW_STOCK, DEFAULT_CONF_ALLOW_STOCK)
    options_allow_tasks = entry.options.get(CONF_ALLOW_TASKS, DEFAULT_CONF_ALLOW_TASKS)

    for sensor in SENSOR_TYPES:
        if options_allow_chores and sensor.startswith(CHORES_NAME):
            _LOGGER.debug("Adding chores sensor")
            device_name = CHORES_NAME
            async_add_entities(
                [GrocySensor(coordinator, entry, device_name, sensor)], True
            )
        elif options_allow_meal_plan and sensor.startswith(MEAL_PLAN_NAME):
            _LOGGER.debug("Adding meal plan sensor")
            device_name = MEAL_PLAN_NAME
            async_add_entities(
                [GrocySensor(coordinator, entry, device_name, sensor)], True
            )
        elif options_allow_shopping_list and sensor.startswith(SHOPPING_LIST_NAME):
            _LOGGER.debug("Adding shopping list sensor")
            device_name = SHOPPING_LIST_NAME
            async_add_entities(
                [GrocySensor(coordinator, entry, device_name, sensor)], True
            )
        elif options_allow_stock and sensor.startswith(STOCK_NAME):
            _LOGGER.debug("Adding stock sensor")
            device_name = STOCK_NAME
            async_add_entities(
                [GrocySensor(coordinator, entry, device_name, sensor)], True
            )
        elif options_allow_tasks and sensor.startswith(TASKS_NAME):
            _LOGGER.debug("Adding tasks sensor")
            device_name = TASKS_NAME
            async_add_entities(
                [GrocySensor(coordinator, entry, device_name, sensor)], True
            )


class GrocySensor(GrocyEntity):
    """Grocy Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SENSOR}"

    # @property
    # def state(self):
    #     """Return the state of the sensor."""
    #     return self.coordinator.data.get("static")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON
