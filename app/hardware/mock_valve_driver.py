class MockValveDriver:
    def __init__(self, valves_count: int = 80):
        self.valves_count = valves_count
        self.valves = [False] * valves_count

    def set_valve(self, valve_number: int, state: bool) -> None:
        if not 1 <= valve_number <= self.valves_count:
            raise ValueError(f"Valve number out of range: {valve_number}")

        self.valves[valve_number - 1] = state
        print(f"[MOCK] Valve {valve_number} -> {'ON' if state else 'OFF'}")

    def get_valve_state(self, valve_number: int) -> bool:
        if not 1 <= valve_number <= self.valves_count:
            raise ValueError(f"Valve number out of range: {valve_number}")

        return self.valves[valve_number - 1]

    def get_all_states(self) -> list[bool]:
        return self.valves.copy()

    def reset_all(self) -> None:
        self.valves = [False] * self.valves_count
        print("[MOCK] All valves reset to OFF")