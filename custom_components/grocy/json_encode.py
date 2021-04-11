import json
from typing import Any

from pygrocy.data_models.product import ProductBarcode


class GrocyJSONEncoder(json.JSONEncoder):
    """Custom JSONEncoder for Grocy"""

    def default(self, o: Any) -> Any:
        """Convert special objects."""

        if isinstance(o, ProductBarcode):
            return o.barcode

        return json.JSONEncoder.default(self, o)