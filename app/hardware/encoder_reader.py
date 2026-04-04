import threading
import time
from dataclasses import dataclass

import serial


@dataclass
class EncoderSnapshot:
    angle: int = 0
    rpm: float = 0.0
    turn_signal: bool = False   # Z
    turn_pulse: bool = False    # T
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
        self._turn_pulse = False
        self._is_connected = False
        self._last_line = ""

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
            turn_pulse = self._turn_pulse

            # импульсные флаги читаем один раз
            self._turn_signal = False
            self._turn_pulse = False

            return EncoderSnapshot(
                angle=self._angle,
                rpm=self._rpm,
                turn_signal=turn_signal,
                turn_pulse=turn_pulse,
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

                    angle, rpm, turn_signal, turn_pulse = parsed

                    with self._lock:
                        self._angle = angle
                        self._rpm = rpm
                        self._last_line = line
                        self._is_connected = True

                        if turn_signal:
                            self._turn_signal = True

                        if turn_pulse:
                            self._turn_pulse = True

            except Exception as e:
                print(f"[ENCODER] Reader error: {e}")

                with self._lock:
                    self._is_connected = False
                    self._rpm = 0.0
                    self._turn_signal = False
                    self._turn_pulse = False

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
    def _parse_line(line: str) -> tuple[int, float, bool, bool] | None:
        """
        Формат:
            A:123 R:16.6 Z:0 T:1
        """
        try:
            parts = line.split()
            if len(parts) != 4:
                return None

            fields: dict[str, str] = {}

            for part in parts:
                if ":" not in part:
                    return None
                key, value = part.split(":", 1)
                fields[key] = value

            if "A" not in fields or "R" not in fields or "Z" not in fields or "T" not in fields:
                return None

            angle = int(fields["A"])
            rpm = float(fields["R"])
            turn_signal = int(fields["Z"]) == 1
            turn_pulse = int(fields["T"]) == 1

            return angle, rpm, turn_signal, turn_pulse

        except Exception:
            return None