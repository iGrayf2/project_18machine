from app.core.engine import MachineEngine
from app.hardware.hardware_manager import HardwareManager


recipe = {
    "id": 1,
    "name": "Тестовый рецепт",
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
}


def print_status(title: str, engine: MachineEngine, hardware: HardwareManager):
    print(f"\n--- {title} ---")
    print(engine.get_status_snapshot())
    print("Valves 1..5:", hardware.get_all_valves()[:5])


hardware = HardwareManager()
engine = MachineEngine(hardware)
engine.load_recipe(recipe)

print_status("После загрузки рецепта", engine, hardware)

# ===== ЦИКЛ 1, ОБОРОТ 1 =====
angles_turn_1 = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

for angle in angles_turn_1:
    engine.update(angle=angle, rpm=30, turn_signal=False)

print_status("Цикл 1, оборот 1 завершен", engine, hardware)

# фронт датчика оборота
engine.update(angle=110, rpm=30, turn_signal=True)
engine.update(angle=120, rpm=30, turn_signal=False)

print_status("Переход на оборот 2", engine, hardware)

# ===== ЦИКЛ 1, ОБОРОТ 2 =====
angles_turn_2 = [130, 180, 220, 280, 320, 350, 10, 20]

for angle in angles_turn_2:
    engine.update(angle=angle, rpm=30, turn_signal=False)

print_status("Цикл 1, оборот 2 завершен", engine, hardware)

# еще один оборот -> должен перейти на цикл 2
engine.update(angle=30, rpm=30, turn_signal=True)
engine.update(angle=40, rpm=30, turn_signal=False)

print_status("Переход на цикл 2", engine, hardware)

# ===== ЦИКЛ 2, ОБОРОТ 1 =====
angles_turn_3 = [45, 50, 60, 70, 80, 90, 100, 110]

for angle in angles_turn_3:
    engine.update(angle=angle, rpm=30, turn_signal=False)

print_status("Цикл 2, оборот 1 завершен", engine, hardware)