import copy


class RecipeService:
    def __init__(self):
        self.recipes = [
            {
                "id": 1,
                "name": "Мочалка A",
                "repeats": 3,
                "cycles": [
                    {
                        "id": 101,
                        "turns": 2,
                        "events": self._create_empty_events(),
                    },
                    {
                        "id": 102,
                        "turns": 2,
                        "events": self._create_empty_events(),
                    },
                ],
            },
            {
                "id": 2,
                "name": "Мочалка B",
                "repeats": 5,
                "cycles": [
                    {
                        "id": 201,
                        "turns": 3,
                        "events": self._create_empty_events(),
                    }
                ],
            },
        ]

        self.recipes[0]["cycles"][0]["events"][1] = {"valve": 2, "event": "on", "angle": 45}
        self.recipes[0]["cycles"][0]["events"][3] = {"valve": 4, "event": "off", "angle": 90}

        self._next_recipe_id = 3
        self._next_cycle_id = 202

    def _create_empty_events(self) -> list[dict]:
        return [
            {"valve": i + 1, "event": "", "angle": 0}
            for i in range(80)
        ]

    def get_all_recipes(self) -> list[dict]:
        return copy.deepcopy(self.recipes)

    def get_recipe_by_id(self, recipe_id: int) -> dict | None:
        for recipe in self.recipes:
            if recipe["id"] == recipe_id:
                return copy.deepcopy(recipe)
        return None

    def get_recipe_short_list(self) -> list[dict]:
        return [{"id": r["id"], "name": r["name"]} for r in self.recipes]

    def get_first_recipe(self) -> dict | None:
        if not self.recipes:
            return None
        return copy.deepcopy(self.recipes[0])

    def replace_all_recipes(self, recipes: list[dict]) -> None:
        cleaned = []

        for recipe in recipes:
            cleaned_recipe = {
                "id": int(recipe["id"]),
                "name": str(recipe.get("name", "")).strip() or "Без названия",
                "repeats": max(1, int(recipe.get("repeats", 1))),
                "cycles": [],
            }

            cycles = recipe.get("cycles", [])
            if not cycles:
                continue

            for cycle in cycles:
                cleaned_cycle = {
                    "id": int(cycle["id"]),
                    "turns": max(1, int(cycle.get("turns", 1))),
                    "events": [],
                }

                events = cycle.get("events", [])
                normalized_events = []
                for index in range(80):
                    if index < len(events):
                        event = events[index]
                        valve = int(event.get("valve", index + 1))
                        action = event.get("event", "")
                        angle = int(event.get("angle", 0))
                    else:
                        valve = index + 1
                        action = ""
                        angle = 0

                    if action not in ("", "on", "off"):
                        action = ""

                    if angle < 0:
                        angle = 0
                    if angle > 360:
                        angle = 360

                    normalized_events.append({
                        "valve": valve,
                        "event": action,
                        "angle": angle,
                    })

                cleaned_cycle["events"] = normalized_events
                cleaned_recipe["cycles"].append(cleaned_cycle)

            if cleaned_recipe["cycles"]:
                cleaned.append(cleaned_recipe)

        if cleaned:
            self.recipes = cleaned
            self._recalculate_ids()

    def _recalculate_ids(self) -> None:
        max_recipe_id = 0
        max_cycle_id = 0

        for recipe in self.recipes:
            max_recipe_id = max(max_recipe_id, int(recipe["id"]))
            for cycle in recipe.get("cycles", []):
                max_cycle_id = max(max_cycle_id, int(cycle["id"]))

        self._next_recipe_id = max_recipe_id + 1
        self._next_cycle_id = max_cycle_id + 1

    def create_recipe_template(self) -> dict:
        recipe = {
            "id": self._next_recipe_id,
            "name": f"Новый рецепт {self._next_recipe_id}",
            "repeats": 1,
            "cycles": [
                {
                    "id": self._next_cycle_id,
                    "turns": 1,
                    "events": self._create_empty_events(),
                }
            ],
        }
        self._next_recipe_id += 1
        self._next_cycle_id += 1
        return recipe