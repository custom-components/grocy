import json
import datetime
from pathlib import Path
from typing import Any

from pygrocy.data_models.product import ProductBarcode
from pygrocy.grocy_api_client import ProductBarcodeData


class GrocyJSONEncoder(json.JSONEncoder):
    """Custom JSONEncoder for Grocy"""

    def default(self, o: Any) -> Any:
        """Convert special objects."""

        if isinstance(o, (ProductBarcode, ProductBarcodeData)):
            return o.barcode
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
            return o.isoformat()
        if isinstance(o, set):
            return list(o)
        if isinstance(o, Path):
            return str(o)
        if hasattr(o, "as_dict"):
            return o.as_dict()

        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            return {"__type": str(type(o)), "repr": repr(o), "str": str(o)}
