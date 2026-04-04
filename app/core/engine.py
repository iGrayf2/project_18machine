import time

from app.core.machine_state import MachineState
from app.hardware.hardware_manager import HardwareManager


class MachineEngine:
    def __init__(self, hardware_manager: HardwareManager):
        self.hardware = hardware_manager
        self.machine_state = MachineState()

        self.recipe = None

        self.current_cycle_index = 0
        self.current_turn_in_cycle = 1
        self.current_recipe_repeat = 1

        self.last_angle = 0
        self.last_turn_signal = False
        self.last_turn_pulse = False

        # Через сколько без движения считаем, что машина стоит
        self.motion_timeout_sec = 0.5
        self.last_motion_ts = time.monotonic()

        # Храним уже выполненные события как уникальные ключи:
        # (valve, angle, event)
        self.executed_event_keys = set()

    def load_recipe(self, recipe: dict) -> None:
        self.recipe = recipe

        self.current_cycle_index = 0
        self.current_turn_in_cycle = 1
        self.current_recipe_repeat = 1

        self.last_angle = 0
        self.last_turn_signal = False
        self.last_turn_pulse = False
        self.last_motion_ts = time.monotonic()
        self.executed_event_keys = set()

        self.machine_state.selected_recipe_id = recipe.get("id")
        self.machine_state.selected_recipe_name = recipe.get("name")
        self.machine_state.recipe_repeats_target = recipe.get("repeats", 1)
        self.machine_state.cycles_total = len(recipe.get("cycles", []))
        self.machine_state.current_cycle_index = 1
        self.machine_state.current_cycle_turn = 1
        self.machine_state.current_recipe_repeat = 1
        self.machine_state.current_cycle_turn_target = (
            self.get_current_cycle().get("turns", 0) if self.get_current_cycle() else 0
        )
        self.machine_state.state = "paused"
        self.machine_state.valves = self.hardware.get_all_valves()

    def reset_to_cycle_1(self) -> None:
        self.current_cycle_index = 0
        self.current_turn_in_cycle = 1
        self.current_recipe_repeat = 1
        self.last_angle = 0
        self.last_turn_signal = False
        self.last_turn_pulse = False
        self.last_motion_ts = time.monotonic()
        self.executed_event_keys = set()

        self.machine_state.current_cycle_index = 1
        self.machine_state.current_cycle_turn = 1
        self.machine_state.current_recipe_repeat = 1

        cycle = self.get_current_cycle()
        self.machine_state.current_cycle_turn_target = cycle.get("turns", 0) if cycle else 0

    def update(self, angle: int, rpm: float, turn_signal: bool, turn_pulse: bool) -> None:
        self.machine_state.encoder_angle = angle
        self.machine_state.rpm = rpm

        if self.recipe is None:
            self.machine_state.state = "idle"
            return

        now = time.monotonic()

        # Считаем, что движение есть, если:
        # 1) угол изменился
        # 2) или пришел Z
        if angle != self.last_angle or turn_signal:
            self.last_motion_ts = now

        is_moving = (now - self.last_motion_ts) <= self.motion_timeout_sec

        if not is_moving:
            self.machine_state.state = "paused"
            self.last_angle = angle
            self.last_turn_signal = turn_signal
            self.last_turn_pulse = turn_pulse
            self.machine_state.valves = self.hardware.get_all_valves()
            return

        self.machine_state.state = "running"

        cycle = self.get_current_cycle()
        if cycle is None:
            return

        # Пока оставляем твою текущую логику:
        # события только на первом обороте текущего цикла
        if self.current_turn_in_cycle == 1:
            self._process_cycle_events(angle, cycle)

        # Полный оборот машины считаем по turn_pulse
        if self._is_new_turn_pulse(turn_pulse):
            self._advance_turn_or_cycle()

        self.last_angle = angle
        self.last_turn_signal = turn_signal
        self.last_turn_pulse = turn_pulse

        self.machine_state.current_cycle_index = self.current_cycle_index + 1
        self.machine_state.current_cycle_turn = self.current_turn_in_cycle
        self.machine_state.current_recipe_repeat = self.current_recipe_repeat
        self.machine_state.current_cycle_turn_target = cycle.get("turns", 0)
        self.machine_state.valves = self.hardware.get_all_valves()

    def _process_cycle_events(self, current_angle: int, cycle: dict) -> None:
        events = cycle.get("events", [])
        pending_updates: list[tuple[int, bool]] = []

        for event in events:
            valve_number = event["valve"]
            event_angle = event["angle"]
            event_action = event["event"]

            event_key = (valve_number, event_angle, event_action)
            if event_key in self.executed_event_keys:
                continue

            if self._angle_passed(event_angle, current_angle):
                state = event_action == "on"
                pending_updates.append((valve_number, state))
                self.executed_event_keys.add(event_key)

        if pending_updates:
            deduped_updates = self._dedupe_keep_last(pending_updates)
            self.hardware.set_valves_bulk(deduped_updates)

    def _dedupe_keep_last(self, updates: list[tuple[int, bool]]) -> list[tuple[int, bool]]:
        result_map: dict[int, bool] = {}

        for valve_number, state in updates:
            result_map[valve_number] = state

        return list(result_map.items())

    def _advance_turn_or_cycle(self) -> None:
        cycle = self.get_current_cycle()
        if cycle is None:
            return

        cycle_turns = cycle.get("turns", 1)

        if self.current_turn_in_cycle < cycle_turns:
            self.current_turn_in_cycle += 1
            return

        self._next_cycle()

    def _next_cycle(self) -> None:
        self.current_cycle_index += 1

        if self.current_cycle_index >= len(self.recipe.get("cycles", [])):
            self.current_cycle_index = 0
            self.current_recipe_repeat += 1

            recipe_repeats = self.recipe.get("repeats", 1)
            if self.current_recipe_repeat > recipe_repeats:
                self.current_recipe_repeat = 1

        self.current_turn_in_cycle = 1
        self.executed_event_keys = set()

    def _is_new_turn_pulse(self, turn_pulse: bool) -> bool:
        return (not self.last_turn_pulse) and turn_pulse

    def _angle_passed(self, event_angle: int, current_angle: int) -> bool:
        if self.last_angle <= current_angle:
            return self.last_angle <= event_angle <= current_angle

        return event_angle >= self.last_angle or event_angle <= current_angle

    def get_current_cycle(self):
        if self.recipe is None:
            return None

        cycles = self.recipe.get("cycles", [])
        if not cycles:
            return None

        if self.current_cycle_index < 0 or self.current_cycle_index >= len(cycles):
            return None

        return cycles[self.current_cycle_index]

    def get_status_snapshot(self) -> dict:
        return self.machine_state.to_dict()