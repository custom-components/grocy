"""Constants for Grocy."""
from enum import Enum

# Base component constants
NAME = "Grocy"
DOMAIN = "grocy"
VERSION = "v3.2.0"

ISSUE_URL = "https://github.com/custom-components/grocy/issues"


# Platforms
PLATFORMS = ["binary_sensor", "sensor"]

# Configuration and options
CONF_NAME = "name"

DEFAULT_PORT = 9192
CONF_URL = "url"
CONF_PORT = "port"
CONF_API_KEY = "api_key"
CONF_VERIFY_SSL = "verify_ssl"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""


class GrocyEntityType(str, Enum):
    """Entity type for Grocy entities."""

    CHORES = "Chores"
    EXPIRED_PRODUCTS = "Expired_products"
    EXPIRING_PRODUCTS = "Expiring_products"
    MEAL_PLAN = "Meal_plan"
    MISSING_PRODUCTS = "Missing_products"
    OVERDUE_CHORES = "Overdue_chores"
    OVERDUE_TASKS = "Overdue_tasks"
    PRODUCTS = "Products"
    SHOPPING_LIST = "Shopping_list"
    STOCK = "Stock"
    TASKS = "Tasks"


class GrocyEntityUnit(str, Enum):
    """Unit of measurement for Grocy entities."""

    CHORES = "Chore(s)"
    MEAL_PLAN = "Meal(s)"
    PRODUCTS = "Product(s)"
    TASKS = "Task(s)"


class GrocyEntityIcon(str, Enum):
    """Icon for a Grocy entity."""

    DEFAULT = "mdi:format-quote-close"

    CHORES = "mdi:broom"
    EXPIRED_PRODUCTS = "mdi:delete-alert-outline"
    EXPIRING_PRODUCTS = "mdi:clock-fast"
    MEAL_PLAN = "mdi:silverware-variant"
    MISSING_PRODUCTS = "mdi:flask-round-bottom-empty-outline"
    OVERDUE_CHORES = "mdi:alert-circle-check-outline"
    OVERDUE_TASKS = "mdi:alert-circle-check-outline"
    PRODUCTS = "mdi:food-fork-drink"
    SHOPPING_LIST = "mdi:cart-outline"
    STOCK = "mdi:fridge-outline"
    TASKS = "mdi:checkbox-marked-circle-outline"

