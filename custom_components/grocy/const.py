"""Constants for grocy."""
# Base component constants
DOMAIN = "grocy"
DOMAIN_DATA = "{}_data".format(DOMAIN)
VERSION = "0.3.0"
PLATFORMS = ["sensor", "binary_sensor"]
REQUIRED_FILES = [
    "const.py",
    "manifest.json",
    "sensor.py",
    "binary_sensor.py",
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

# Configuration
CONF_SENSOR = "sensor"
CONF_BINARY_SENSOR = "binary_sensor"
CONF_ENABLED = "enabled"
CONF_NAME = "name"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_PORT_NUMBER = 9192
