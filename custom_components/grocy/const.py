"""Constants for grocy."""
# Base component constants
DOMAIN = "grocy"
DOMAIN_DATA = "{}_data".format(DOMAIN)
VERSION = "0.1.3"
PLATFORMS = ["sensor"]
REQUIRED_FILES = [
    "const.py",
    "manifest.json",
    "sensor.py",
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
SENSOR_UNIT_OF_MEASUREMENT = "Product(s)"

# Configuration
CONF_SENSOR = "sensor"
CONF_ENABLED = "enabled"
CONF_NAME = "name"

# Defaults
DEFAULT_NAME = DOMAIN
