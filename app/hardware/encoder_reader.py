import threading
import time
from dataclasses import dataclass

import serial


@dataclass
class EncoderSnapshot:
    angle: int = 0
    rpm: float = 0.0
    turn_signal: bool = False
    is_connected: bool = False
    raw_line: str = ""


class EncoderReader:
    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 0.2,
        reconnect_delay: float = 2.0,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.reconnect_delay = reconnect_delay

        self._ser: serial.Serial | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        self._angle = 0
        self._rpm = 0.0
        self._turn_signal = False
        self._is_connected = False
        self._last_line = ""
        self._last_turn_ts = 0.0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self._close_serial()

    def get_snapshot(self) -> EncoderSnapshot:
        with self._lock:
            turn_signal = self._turn_signal

            # turn_signal должен быть кратковременным импульсом
            # один раз прочитали -> сбрасываем
            self._turn_signal = False

            return EncoderSnapshot(
                angle=self._angle,
                rpm=self._rpm,
                turn_signal=turn_signal,
                is_connected=self._is_connected,
                raw_line=self._last_line,
            )

    def _reader_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._open_serial()

                while not self._stop_event.is_set():
                    line = self._ser.readline().decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue

                    parsed = self._parse_line(line)
                    if parsed is None:
                        continue

                    angle, rpm, turn_signal = parsed

                    with self._lock:
                        self._angle = angle
                        self._rpm = rpm
                        self._last_line = line
                        self._is_connected = True

                        if turn_signal:
                            self._turn_signal = True
                            self._last_turn_ts = time.time()

            except Exception as e:
                print(f"[ENCODER] Reader error: {e}")
                with self._lock:
                    self._is_connected = False
                    self._rpm = 0.0

                self._close_serial()

                if not self._stop_event.is_set():
                    time.sleep(self.reconnect_delay)

    def _open_serial(self) -> None:
        if self._ser and self._ser.is_open:
            return

        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            write_timeout=self.timeout,
        )

        # ESP32 может перезагружаться при открытии COM
        time.sleep(2.0)
        self._ser.reset_input_buffer()

        print(f"[ENCODER] Connected to {self.port} @ {self.baudrate}")

    def _close_serial(self) -> None:
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        except Exception:
            pass
        finally:
            self._ser = None

    @staticmethod
    def _parse_line(line: str) -> tuple[int, float, bool] | None:
        # Ждем строки вида:
        # A:123 R:16.6 Z:0
        try:
            parts = line.split()
            if len(parts) != 3:
                return None

            a_part, r_part, z_part = parts

            if not a_part.startswith("A:"):
                return None
            if not r_part.startswith("R:"):
                return None
            if not z_part.startswith("Z:"):
                return None

            angle = int(a_part[2:])
            rpm = float(r_part[2:])
            z_value = int(z_part[2:])

            turn_signal = z_value == 1
            return angle, rpm, turn_signal

        except Exception:
            return None