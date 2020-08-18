"""Constants for grocy."""
import logging

LOGGER = logging.getLogger(__package__)

# Base component constants
DOMAIN = "grocy"
VERSION = "1.2.0"
REQUIRED_FILES = [
    "const.py",
    "manifest.json",
    "sensor.py",
    "binary_sensor.py",
    "config_flow.py",
    "translations/en.json",
]
ISSUE_URL = "https://github.com/custom-components/grocy/issues"
ATTRIBUTION = "Data from this is provided by grocy."
STARTUP = """
-------------------------------------------------------------------
{name}
Version: {version}
This is a custom component
If you have any issues with this you need to open an issue here:
{issueurl}
-------------------------------------------------------------------
"""

# Icons
ICON = "mdi:format-quote-close"

# Device classes
SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT = "Product(s)"
SENSOR_CHORES_UNIT_OF_MEASUREMENT = "Chore(s)"
SENSOR_TASKS_UNIT_OF_MEASUREMENT = "Task(s)"
SENSOR_MEALS_UNIT_OF_MEASUREMENT = "Meal(s)"

STOCK_NAME = "stock"
CHORES_NAME = "chores"
TASKS_NAME = "tasks"
SHOPPING_LIST_NAME = "shopping_list"
PRODUCTS_NAME = "products"
EXPIRING_PRODUCTS_NAME = "expiring_products"
EXPIRED_PRODUCTS_NAME = "expired_products"
MISSING_PRODUCTS_NAME = "missing_products"
MEAL_PLAN_NAME = "meal_plan"


SUPPORTED_PLATFORMS = ["binary_sensor", "sensor"]
SENSOR_TYPES = [STOCK_NAME, CHORES_NAME, TASKS_NAME, SHOPPING_LIST_NAME, MEAL_PLAN_NAME]
BINARY_SENSOR_TYPES = [
    EXPIRING_PRODUCTS_NAME,
    EXPIRED_PRODUCTS_NAME,
    MISSING_PRODUCTS_NAME,
]

NEW_SENSOR = "sensors"
NEW_BINARY_SENSOR = "binary_sensors"

# Configuration
CONF_ENABLED = "enabled"
CONF_NAME = "name"

CONF_ALLOW_CHORES = "allow_chores"
CONF_ALLOW_MEAL_PLAN = "allow_meal_plan"
CONF_ALLOW_PRODUCTS = "allow_products"
CONF_ALLOW_SHOPPING_LIST = "allow_shopping_list"
CONF_ALLOW_STOCK = "allow_stock"
CONF_ALLOW_TASKS = "allow_tasks"

# Defaults
DEFAULT_CONF_NAME = DOMAIN
DEFAULT_PORT_NUMBER = 9192
DEFAULT_CONF_ALLOW_CHORES = False
DEFAULT_CONF_ALLOW_MEAL_PLAN = False
DEFAULT_CONF_ALLOW_PRODUCTS = True
DEFAULT_CONF_ALLOW_SHOPPING_LIST = False
DEFAULT_CONF_ALLOW_STOCK = True
DEFAULT_CONF_ALLOW_TASKS = False
