"""Constants for Grocy."""
# Base component constants
NAME = "Grocy"
DOMAIN = "grocy"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"

ISSUE_URL = "https://github.com/custom-components/grocy/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
# BINARY_SENSOR_DEVICE_CLASS = "connectivity"

SENSOR_PRODUCTS_UNIT_OF_MEASUREMENT = "Product(s)"
SENSOR_CHORES_UNIT_OF_MEASUREMENT = "Chore(s)"
SENSOR_TASKS_UNIT_OF_MEASUREMENT = "Task(s)"
SENSOR_MEALS_UNIT_OF_MEASUREMENT = "Meal(s)"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
# PLATFORMS = [BINARY_SENSOR, SENSOR, SWITCH]
PLATFORMS = [BINARY_SENSOR, SENSOR]

# Entities
STOCK_NAME = "Stock"
CHORES_NAME = "Chores"
TASKS_NAME = "Tasks"
SHOPPING_LIST_NAME = "Shopping_list"
PRODUCTS_NAME = "Products"
EXPIRING_PRODUCTS_NAME = "Expiring_products"
EXPIRED_PRODUCTS_NAME = "Expired_products"
MISSING_PRODUCTS_NAME = "Missing_products"
MEAL_PLAN_NAME = "Meal_plan"

SENSOR_TYPES = [STOCK_NAME, CHORES_NAME, TASKS_NAME, SHOPPING_LIST_NAME, MEAL_PLAN_NAME]
BINARY_SENSOR_TYPES = [
    EXPIRING_PRODUCTS_NAME,
    EXPIRED_PRODUCTS_NAME,
    MISSING_PRODUCTS_NAME,
]

ALL_ENTITY_TYPES = [
    STOCK_NAME,
    CHORES_NAME,
    TASKS_NAME,
    SHOPPING_LIST_NAME,
    MEAL_PLAN_NAME,
    EXPIRING_PRODUCTS_NAME,
    EXPIRED_PRODUCTS_NAME,
    MISSING_PRODUCTS_NAME,
]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_NAME = "name"

DEFAULT_CONF_NAME = DOMAIN
DEFAULT_PORT = 9192
CONF_URL = "url"
CONF_PORT = "port"
CONF_API_KEY = "api_key"
CONF_VERIFY_SSL = "verify_ssl"

CONF_ALLOW_CHORES = "allow_chores"
CONF_ALLOW_MEAL_PLAN = "allow_meal_plan"
CONF_ALLOW_PRODUCTS = "allow_products"
CONF_ALLOW_SHOPPING_LIST = "allow_shopping_list"
CONF_ALLOW_STOCK = "allow_stock"
CONF_ALLOW_TASKS = "allow_tasks"

# Defaults
DEFAULT_NAME = DOMAIN
# DEFAULT_CONF_NAME = DOMAIN
DEFAULT_CONF_PORT_NUMBER = 9192
DEFAULT_CONF_ALLOW_CHORES = False
DEFAULT_CONF_ALLOW_MEAL_PLAN = False
DEFAULT_CONF_ALLOW_SHOPPING_LIST = False
DEFAULT_CONF_ALLOW_STOCK = False
DEFAULT_CONF_ALLOW_TASKS = False

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

REQUIRED_FILES = [
    "const.py",
    "entity.py",
    "grocy_data.py",
    "manifest.json",
    "helpers.py",
    "sensor.py",
    "binary_sensor.py",
    "config_flow.py",
    "services.py",
    "translations/en.json",
]
