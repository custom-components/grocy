"""Helpers for Grocy."""

import base64
from typing import Any, Dict, Tuple
from urllib.parse import urlparse


def extract_base_url_and_path(url: str) -> Tuple[str, str]:
    """Extract the base url and path from a given URL."""
    parsed_url = urlparse(url)

    return (f"{parsed_url.scheme}://{parsed_url.netloc}", parsed_url.path.strip("/"))


class MealPlanItem(object):
    """Grocy meal plan item definition."""

    def __init__(self, data):
        self.day = data.day
        self.note = data.note
        self.recipe_name = data.recipe.name if data.recipe else None
        self.desired_servings = data.recipe.desired_servings if data.recipe else None

        if data.recipe and data.recipe.picture_file_name is not None:
            b64name = base64.b64encode(data.recipe.picture_file_name.encode("ascii"))
            self.picture_url = f"/api/grocy/recipepictures/{str(b64name, 'utf-8')}"
        else:
            self.picture_url = None

    def as_dict(self) -> Dict[str, Any]:
        """Return dictionary for object."""
        return vars(self)
