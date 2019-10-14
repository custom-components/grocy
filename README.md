## Installation instructions:

1. Install HACS for Home Assistant
2. Go to Community-Store-Grocy
3. Install Grocy
4. Restart Home Assistant
5. Go to Grocy-Wrench icon-Manage API keys-Add
6. Copy resulting API key and Grocy URL and input this in configuration.yaml:

```yaml
grocy:
  url: "https://{{YOUR_GROCY_URL}}"
  api_key: "{{YOUR_GROCY_API_KEY}}"
  verify_ssl: true
  port: 9192
  sensor:
    - 'stock'
    - 'chores'
  binary_sensor:
    - enabled : true
```

7. Restart Home Assistant
8. Look for the new Grocy sensor in States and use its info

---
[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/X8X1LYUK)
