from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MachineState:
    selected_recipe_id: Optional[int] = None
    selected_recipe_name: Optional[str] = None

    recipe_repeats_target: int = 1
    current_recipe_repeat: int = 1

    current_cycle_index: int = 1
    cycles_total: int = 0

    current_cycle_turn: int = 1
    current_cycle_turn_target: int = 0

    encoder_angle: int = 0
    rpm: int = 0

    state: str = "paused"  # running / paused / idle / error

    encoder_ok: bool = True
    turn_sensor_ok: bool = True

    valves: list[bool] = field(default_factory=lambda: [False] * 80)

    def to_dict(self) -> dict:
        return {
            "selected_recipe_id": self.selected_recipe_id,
            "selected_recipe_name": self.selected_recipe_name,
            "recipe_repeats_target": self.recipe_repeats_target,
            "current_recipe_repeat": self.current_recipe_repeat,
            "current_cycle_index": self.current_cycle_index,
            "cycles_total": self.cycles_total,
            "current_cycle_turn": self.current_cycle_turn,
            "current_cycle_turn_target": self.current_cycle_turn_target,
            "encoder_angle": self.encoder_angle,
            "rpm": self.rpm,
            "state": self.state,
            "encoder_ok": self.encoder_ok,
            "turn_sensor_ok": self.turn_sensor_ok,
            "valves": self.valves,
        }