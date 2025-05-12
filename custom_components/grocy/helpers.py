"""Helpers for Grocy."""
from __future__ import annotations

import json
import base64
from typing import Any, Dict, Tuple
from urllib.parse import urlparse

from pygrocy2.data_models.meal_items import MealPlanItem
from pygrocy2.data_models.product import Product
from pygrocy2.grocy_api_client import CurrentStockResponse


def extract_base_url_and_path(url: str) -> Tuple[str, str]:
    """Extract the base url and path from a given URL."""
    parsed_url = urlparse(url)

    return (f"{parsed_url.scheme}://{parsed_url.netloc}", parsed_url.path.strip("/"))


class MealPlanItemWrapper:
    """Wrapper around the pygrocy MealPlanItem."""

    def __init__(self, meal_plan: MealPlanItem):
        self._meal_plan = meal_plan

    @property
    def meal_plan(self) -> MealPlanItem:
        """The pygrocy MealPlanItem."""
        return self._meal_plan

    @property
    def picture_url(self) -> str | None:
        """Proxy URL to the picture."""
        recipe = self.meal_plan.recipe
        if recipe and recipe.picture_file_name:
            b64name = base64.b64encode(recipe.picture_file_name.encode("ascii"))
            return f"/api/grocy/recipepictures/{str(b64name, 'utf-8')}"
        return None

    def as_dict(self) -> Dict[str, Any]:
        """Return attributes for the pygrocy MealPlanItem object including picture URL."""
        props = self.meal_plan.as_dict()
        props["picture_url"] = self.picture_url
        return props
    
class ProductWrapper:
    """Wrapper around the pygrocy CurrentStockResponse."""

    def __init__(self, product: CurrentStockResponse, hass):
        self._product = Product(product)
        self._hass = hass
        self._picture_url = self.get_picture_url(product)

    @property
    def product(self) -> Product:
        """The pygrocy Product."""
        return self._product

    @property
    def picture_url(self) -> str | None:
        """Proxy URL to the picture."""
        return self._picture_url

    def get_picture_url(self, product: CurrentStockResponse) -> str | None:
        """Proxy URL to the picture."""
        
        if product.product and product.product.picture_file_name:
            b64name = base64.b64encode(product.product.picture_file_name.encode("ascii"))
            return f"/api/grocy/productpictures/{str(b64name, 'utf-8')}"
        
        return None        

    def as_dict(self) -> Dict[str, Any]:
        """Return attributes for the pygrocy Product object including picture URL."""        
        props = self.product.as_dict()
        props["picture_url"] = self.picture_url
        return props