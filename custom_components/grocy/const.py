"""Constants for Grocy."""
from datetime import timedelta
from typing import Final

NAME: Final = "Grocy"
DOMAIN: Final = "grocy"
VERSION = "0.0.0"

ISSUE_URL: Final = "https://github.com/custom-components/grocy/issues"

PLATFORMS: Final = ["binary_sensor", "sensor", "todo"]

SCAN_INTERVAL = timedelta(seconds=30)

DEFAULT_PORT: Final = 9192
CONF_URL: Final = "url"
CONF_PORT: Final = "port"
CONF_API_KEY: Final = "api_key"
CONF_VERIFY_SSL: Final = "verify_ssl"

STARTUP_MESSAGE: Final = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

CHORES: Final = "Chore(s)"
MEAL_PLANS: Final = "Meal(s)"
PRODUCTS: Final = "Product(s)"
TASKS: Final = "Task(s)"
ITEMS: Final = "Item(s)"

ATTR_BATTERIES: Final = "batteries"
ATTR_CHORES: Final = "chores"
ATTR_EXPIRED_PRODUCTS: Final = "expired_products"
ATTR_EXPIRING_PRODUCTS: Final = "expiring_products"
ATTR_MEAL_PLAN: Final = "meal_plan"
ATTR_MISSING_PRODUCTS: Final = "missing_products"
ATTR_OVERDUE_BATTERIES: Final = "overdue_batteries"
ATTR_OVERDUE_CHORES: Final = "overdue_chores"
ATTR_OVERDUE_PRODUCTS: Final = "overdue_products"
ATTR_OVERDUE_TASKS: Final = "overdue_tasks"
ATTR_SHOPPING_LIST: Final = "shopping_list"
ATTR_STOCK: Final = "stock"
ATTR_TASKS: Final = "tasks"
