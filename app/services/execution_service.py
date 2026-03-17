from app.core.engine import MachineEngine
from app.hardware.hardware_manager import HardwareManager
from app.services.recipe_service import RecipeService


class ExecutionService:
    def __init__(self):
        self.hardware = HardwareManager()
        self.recipe_service = RecipeService()
        self.engine = MachineEngine(self.hardware)

        first_recipe = self.recipe_service.get_first_recipe()
        if first_recipe:
            self.engine.load_recipe(first_recipe)

        self._sim_angle = 0
        self._sim_rpm = 30
        self._sim_turn_signal = False

    def select_recipe(self, recipe_id: int) -> bool:
        recipe = self.recipe_service.get_recipe_by_id(recipe_id)
        if recipe is None:
            return False

        self.hardware.reset_all_valves()
        self.engine.load_recipe(recipe)
        return True

    def set_recipe_repeats(self, value: int) -> bool:
        if self.engine.recipe is None:
            return False

        if value < 1:
            value = 1

        self.engine.recipe["repeats"] = value
        self.engine.machine_state.recipe_repeats_target = value
        return True

    def reset_to_cycle_1(self) -> None:
        self.engine.reset_to_cycle_1()

    def get_status_snapshot(self) -> dict:
        snapshot = self.engine.get_status_snapshot()
        recipes = self.recipe_service.get_recipe_short_list()
        snapshot["recipes"] = recipes
        snapshot["recipes_count"] = len(recipes)
        return snapshot

    def handle_action(self, payload: dict) -> dict | None:
        action = payload.get("action")

        if action == "select_recipe":
            recipe_id = payload.get("recipe_id")
            if isinstance(recipe_id, int) and self.select_recipe(recipe_id):
                return {"type": "info", "data": {"message": "Рецепт выбран"}}
            return {"type": "error", "data": {"message": "Рецепт не найден"}}

        if action == "set_recipe_repeats":
            value = payload.get("value")
            if isinstance(value, int):
                self.set_recipe_repeats(value)
                return {"type": "info", "data": {"message": "Повторы обновлены"}}
            return {"type": "error", "data": {"message": "Неверное значение повторов"}}

        if action == "reset_to_cycle_1":
            self.reset_to_cycle_1()
            return {
                "type": "reset_done",
                "data": {
                    "current_cycle_index": 1,
                    "current_cycle_turn": 1,
                    "current_recipe_repeat": 1,
                },
            }

        return {"type": "error", "data": {"message": f"Неизвестное действие: {action}"}}

    def simulate_step(self) -> None:
        previous_angle = self._sim_angle
        next_angle = previous_angle + 15

        if next_angle > 360:
            next_angle = next_angle - 360
            self._sim_turn_signal = True
        else:
            self._sim_turn_signal = False

        self._sim_angle = next_angle

        self.engine.update(
            angle=self._sim_angle,
            rpm=self._sim_rpm,
            turn_signal=self._sim_turn_signal,
        )