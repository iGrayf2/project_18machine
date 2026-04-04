import os
import threading
import time

from app.core.engine import MachineEngine
from app.hardware.encoder_reader import EncoderReader
from app.hardware.hardware_manager import HardwareManager
from app.services.recipe_service import RecipeService


class ExecutionService:
    def __init__(self):
        self.hardware = HardwareManager()
        self.recipe_service = RecipeService()
        self.engine = MachineEngine(self.hardware)

        self.encoder_mode = os.getenv("ENCODER_MODE", "sim").strip().lower()

        self.encoder_reader: EncoderReader | None = None
        if self.encoder_mode == "real":
            encoder_port = os.getenv("ENCODER_PORT", "COM6")
            encoder_baudrate = int(os.getenv("ENCODER_BAUDRATE", "115200"))

            self.encoder_reader = EncoderReader(
                port=encoder_port,
                baudrate=encoder_baudrate,
            )
            self.encoder_reader.start()
            print(f"[EXECUTION] Encoder REAL mode: {encoder_port} {encoder_baudrate}")
        else:
            print("[EXECUTION] Encoder SIM mode")

        first_recipe = self.recipe_service.get_first_recipe()
        if first_recipe:
            self.engine.load_recipe(first_recipe)

        self._sim_angle = 0
        self._sim_rpm = 30
        self._sim_turn_signal = False
        self._sim_turn_pulse = False

        self._loop_interval = float(os.getenv("ENGINE_LOOP_INTERVAL", "0.05"))  # 50 мс
        self._loop_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self.start_loop()

    def start_loop(self) -> None:
        if self._loop_thread and self._loop_thread.is_alive():
            return

        self._stop_event.clear()
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()
        print(f"[EXECUTION] Engine loop started, interval={self._loop_interval}s")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.update_once()
            except Exception as e:
                print(f"[EXECUTION] Engine loop error: {e}")

            time.sleep(self._loop_interval)

    def update_once(self) -> None:
        if self.encoder_reader:
            enc = self.encoder_reader.get_snapshot()
            self.engine.update(
                angle=enc.angle,
                rpm=enc.rpm,
                turn_signal=enc.turn_signal,
                turn_pulse=enc.turn_pulse,
            )
        else:
            self.simulate_step()

    def close(self) -> None:
        self._stop_event.set()

        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=2.0)

        try:
            if self.encoder_reader:
                self.encoder_reader.stop()
        except Exception as e:
            print(f"[EXECUTION] Encoder close error: {e}")

        try:
            self.hardware.close()
        except Exception as e:
            print(f"[EXECUTION] Hardware close error: {e}")

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

        if self.encoder_reader:
            enc = self.encoder_reader.get_snapshot()
            snapshot["encoder_connected"] = enc.is_connected
            snapshot["encoder_raw_line"] = enc.raw_line
        else:
            snapshot["encoder_connected"] = False
            snapshot["encoder_raw_line"] = ""

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
            self._sim_turn_pulse = True
        else:
            self._sim_turn_signal = False
            self._sim_turn_pulse = False

        self._sim_angle = next_angle

        self.engine.update(
            angle=self._sim_angle,
            rpm=self._sim_rpm,
            turn_signal=self._sim_turn_signal,
            turn_pulse=self._sim_turn_pulse,
        )


execution_service = ExecutionService()