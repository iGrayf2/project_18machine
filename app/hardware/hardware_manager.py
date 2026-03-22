import os

from app.hardware.mock_valve_driver import MockValveDriver
from app.hardware.board_driver import IOBoardDriver


class HardwareManager:
    """
    Единая точка доступа к железу.

    Режимы:
    - mock  -> старая логика через MockValveDriver
    - real  -> реальная плата по COM-порту

    Настройка через переменные окружения:
    - HARDWARE_MODE=mock | real
    - BOARD_PORT=COM5
    - BOARD_BAUDRATE=625000
    - BOARD_CHANNELS=80
    - BOARD_PROTOCOL_CHANNELS=96
    - BOARD_AUTO_INIT=1
    """

    def __init__(self):
        self.mode = os.getenv("HARDWARE_MODE", "mock").strip().lower()
        self.channels_count = int(os.getenv("BOARD_CHANNELS", "80"))

        if self.mode == "real":
            port = os.getenv("BOARD_PORT", "COM5")
            baudrate = int(os.getenv("BOARD_BAUDRATE", "625000"))
            protocol_channels = int(os.getenv("BOARD_PROTOCOL_CHANNELS", "96"))
            auto_init = os.getenv("BOARD_AUTO_INIT", "1").strip() in ("1", "true", "yes", "on")

            self.valve_driver = IOBoardDriver(
                port=port,
                baudrate=baudrate,
                channels_count=self.channels_count,
                protocol_channels=protocol_channels,
                auto_open=True,
                auto_initialize=auto_init,
            )

            print(
                f"[HARDWARE] REAL mode: port={port}, baudrate={baudrate}, "
                f"channels={self.channels_count}, protocol_channels={protocol_channels}"
            )
        else:
            self.mode = "mock"
            self.valve_driver = MockValveDriver(valves_count=self.channels_count)
            print(f"[HARDWARE] MOCK mode: channels={self.channels_count}")

    def set_valve(self, valve_number: int, state: bool) -> None:
        self.valve_driver.set_valve(valve_number, state)

    def get_valve_state(self, valve_number: int) -> bool:
        return self.valve_driver.get_valve_state(valve_number)

    def get_all_valves(self) -> list[bool]:
        return self.valve_driver.get_all_states()

    def reset_all_valves(self) -> None:
        self.valve_driver.reset_all()

    # --- дополнительные методы для реального режима ---
    def initialize_board(self) -> None:
        if hasattr(self.valve_driver, "initialize_board"):
            self.valve_driver.initialize_board()

    def close(self) -> None:
        if hasattr(self.valve_driver, "close"):
            self.valve_driver.close()

    def is_real_mode(self) -> bool:
        return self.mode == "real"