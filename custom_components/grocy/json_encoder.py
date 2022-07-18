"""JSON encoder for Grocy."""

import datetime
from typing import Any

from homeassistant.helpers.json import ExtendedJSONEncoder


class CustomJSONEncoder(ExtendedJSONEncoder):
    """JSONEncoder for compatibility, falls back to the Home Assistant Core ExtendedJSONEncoder."""

    def default(self, o: Any) -> Any:
        """Convert certain objects."""

        if isinstance(o, (datetime.date, datetime.time)):
            return o.isoformat()

        return super().default(o)
