import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pygrocy.data_models.product import ProductBarcode


class GrocyJSONEncoder(json.JSONEncoder):
    """Custom JSONEncoder for Grocy"""

    def default(self, o: Any) -> Any:
        """Convert special objects."""

        if isinstance(o, ProductBarcode):
            return o.barcode
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, set):
            return list(o)
        if isinstance(o, Path):
            return str(o)
        if hasattr(o, "as_dict"):
            return o.as_dict()

        return json.JSONEncoder.default(self, o)
