from app.hardware.mock_valve_driver import MockValveDriver


class HardwareManager:
    def __init__(self):
        self.valve_driver = MockValveDriver()

    def set_valve(self, valve_number: int, state: bool) -> None:
        self.valve_driver.set_valve(valve_number, state)

    def get_valve_state(self, valve_number: int) -> bool:
        return self.valve_driver.get_valve_state(valve_number)

    def get_all_valves(self) -> list[bool]:
        return self.valve_driver.get_all_states()

    def reset_all_valves(self) -> None:
        self.valve_driver.reset_all()