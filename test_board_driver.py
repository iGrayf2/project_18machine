from app.hardware.hardware_manager import HardwareManager


def main() -> None:
    hw = HardwareManager()

    if not hw.is_real_mode():
        print("ОШИБКА: для этого теста нужен режим HARDWARE_MODE=real")
        return

    print("\n--- RESET ALL ---")
    hw.reset_all_valves()

    print("\n--- CH1 ON ---")
    hw.set_valve(1, True)

    print("\n--- CH1 OFF ---")
    hw.set_valve(1, False)

    print("\n--- CH5 ON ---")
    hw.set_valve(5, True)

    print("\n--- CH7 ON ---")
    hw.set_valve(7, True)

    print("\n--- CH12 ON ---")
    hw.set_valve(12, True)

    print("\n--- ALL STATES ---")
    states = hw.get_all_valves()
    on_channels = [i + 1 for i, state in enumerate(states) if state]
    print("Включенные каналы:", on_channels)

    print("\n--- RESET ALL ---")
    hw.reset_all_valves()

    hw.close()
    print("\nГОТОВО")


if __name__ == "__main__":
    main()