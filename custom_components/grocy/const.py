"""Constants for Grocy."""
from typing import Final

NAME: Final = "Grocy"
DOMAIN: Final = "grocy"
VERSION = "0.0.0"

ISSUE_URL: Final = "https://github.com/custom-components/grocy/issues"

PLATFORMS: Final = ["binary_sensor", "sensor"]

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

GROCY_CLIENT = "grocy_client"
GROCY_AVAILABLE_ENTITIES = "available_entities"
REGISTERED_ENTITIES = "registered_entities"

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

SERVICE_ADD_PRODUCT = "add_product_to_stock"
SERVICE_CONSUME_PRODUCT = "consume_product_from_stock"
SERVICE_OPEN_PRODUCT = "open_product"
SERVICE_EXECUTE_CHORE = "execute_chore"
SERVICE_COMPLETE_TASK = "complete_task"
SERVICE_ADD_GENERIC = "add_generic"
SERVICE_CONSUME_RECIPE = "consume_recipe"
SERVICE_TRACK_BATTERY = "track_battery"
