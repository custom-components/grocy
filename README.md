## Installation instructions (general):

1. Install HACS for Home Assistant
2. Go to Community-Store-Grocy
3. Install Grocy
4. Restart Home Assistant
5. Go to Grocy-Wrench icon-Manage API keys-Add
6. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Grocy"
7. Look for the new Grocy sensor in States and use its info


## Additional installation instructions for Hass.io users

The configuration is slightly different for users that use Hass.io and the [official Grocy addon](https://github.com/hassio-addons/addon-grocy) from the Hass.io Add-on store.

1. If you haven't already done so, install Grocy from the Add-on store
2. In the 'Network' section of the add-on config, input 9192 in the host field [screenshot](https://github.com/custom-components/grocy/raw/master/grocy-addon-config.png). Save your changes and restart the add-on.
3. Install HACS for Home Assistant
4. Go to Community > Store > Grocy
5. Install the Grocy integration component
6. Restart Home Assistant
7. Go to Grocy > Wrench icon > Manage API keys > Add
8. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Grocy"
9. Look for the new Grocy sensor in States and use its info

---
[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/X8X1LYUK)
