class RecipeService:
    def __init__(self):
        self.recipes = [
            {
                "id": 1,
                "name": "Мочалка A",
                "repeats": 3,
                "cycles": [
                    {
                        "turns": 2,
                        "events": [
                            {"valve": 1, "event": "on", "angle": 40},
                            {"valve": 2, "event": "off", "angle": 90},
                        ],
                    },
                    {
                        "turns": 2,
                        "events": [
                            {"valve": 1, "event": "off", "angle": 50},
                            {"valve": 3, "event": "on", "angle": 100},
                        ],
                    },
                ],
            },
            {
                "id": 2,
                "name": "Мочалка B",
                "repeats": 5,
                "cycles": [
                    {
                        "turns": 3,
                        "events": [
                            {"valve": 4, "event": "on", "angle": 60},
                            {"valve": 5, "event": "off", "angle": 120},
                        ],
                    }
                ],
            },
        ]

    def get_all_recipes(self) -> list[dict]:
        return self.recipes

    def get_recipe_by_id(self, recipe_id: int) -> dict | None:
        for recipe in self.recipes:
            if recipe["id"] == recipe_id:
                return recipe
        return None

    def get_recipe_short_list(self) -> list[dict]:
        return [{"id": r["id"], "name": r["name"]} for r in self.recipes]

    def get_first_recipe(self) -> dict | None:
        if not self.recipes:
            return None
        return self.recipes[0]