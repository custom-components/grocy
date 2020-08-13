class MealPlanItem(object):
    def __init__(self, data, base_url):
        self.day = data.day
        self.note = data.note
        self.recipe_name = data.recipe.name
        self.desired_servings = data.recipe.desired_servings

        picture_path = data.recipe.get_picture_url_path(400)
        self.picture_url = f"{base_url}/api/{picture_path}"
