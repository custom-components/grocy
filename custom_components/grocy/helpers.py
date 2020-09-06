import base64

class MealPlanItem(object):
    def __init__(self, data):
        self.day = data.day
        self.note = data.note
        self.recipe_name = data.recipe.name
        self.desired_servings = data.recipe.desired_servings

        if data.recipe.picture_file_name is not None:
            b64name = base64.b64encode(data.recipe.picture_file_name.encode("ascii"))
            self.picture_url = f"/api/grocy/recipepictures/{str(b64name, 'utf-8')}"
        else:
            self.picture_url = None

    def as_dict(self):
        return vars(self)
