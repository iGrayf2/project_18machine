import time
from typing import Iterable

import serial


class BoardProtocolError(Exception):
    """Ошибка протокола платы."""


class BoardNotConnectedError(Exception):
    """Порт не открыт."""


class IOBoardDriver:
    """
    Реальный драйвер платы клапанов.

    Совместим по интерфейсу с MockValveDriver:
    - set_valve()
    - get_valve_state()
    - get_all_states()
    - reset_all()

    Дополнительно:
    - open()
    - close()
    - initialize_board()
    - apply_state()
    - ping()
    """

    SHORT_PACKET = bytes([0x9A, 0x05, 0x01, 0x01, 0x5E])
    EXPECTED_ACK = bytes([0xC1, 0x05, 0x01, 0x00, 0x38])

    def __init__(
        self,
        port: str,
        baudrate: int = 625000,
        channels_count: int = 80,
        protocol_channels: int = 96,
        timeout: float = 0.02,
        write_timeout: float = 1.0,
        auto_open: bool = False,
        auto_initialize: bool = False,
    ):
        if channels_count < 1:
            raise ValueError("channels_count должен быть >= 1")
        if protocol_channels < channels_count:
            raise ValueError("protocol_channels не может быть меньше channels_count")
        if protocol_channels % 8 != 0:
            raise ValueError("protocol_channels должен делиться на 8")

        self.port = port
        self.baudrate = baudrate
        self.channels_count = channels_count
        self.protocol_channels = protocol_channels
        self.state_bytes_count = protocol_channels // 8
        self.timeout = timeout
        self.write_timeout = write_timeout

        self._ser: serial.Serial | None = None
        self._state_bytes = [0x00] * self.state_bytes_count
        self._initialized = False

        if auto_open:
            self.open()

        if auto_initialize:
            self.initialize_board()

    # ----------------------------
    # Базовая работа с портом
    # ----------------------------
    def open(self) -> None:
        if self.is_open:
            return

        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
            write_timeout=self.write_timeout,
        )

        time.sleep(0.1)

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()
        self._ser = None

    @property
    def is_open(self) -> bool:
        return self._ser is not None and self._ser.is_open

    @property
    def initialized(self) -> bool:
        return self._initialized

    # ----------------------------
    # Совместимый интерфейс с mock
    # ----------------------------
    def set_valve(self, valve_number: int, state: bool) -> None:
        self._validate_channel(valve_number)
        self._set_channel_bit(valve_number, state)
        self.apply_state()

    def get_valve_state(self, valve_number: int) -> bool:
        self._validate_channel(valve_number)
        byte_index = (valve_number - 1) // 8
        bit_index = (valve_number - 1) % 8
        return bool(self._state_bytes[byte_index] & (1 << bit_index))

    def get_all_states(self) -> list[bool]:
        return [self.get_valve_state(ch) for ch in range(1, self.channels_count + 1)]

    def reset_all(self) -> None:
        for i in range(len(self._state_bytes)):
            self._state_bytes[i] = 0x00
        print("[BOARD] RESET ALL")
        self.apply_state()

    # ----------------------------
    # Дополнительные методы
    # ----------------------------
    def set_valves_bulk(self, states: Iterable[tuple[int, bool]]) -> None:
        """
        Пакетно изменяет несколько клапанов и отправляет один snapshot.
        states: [(1, True), (2, False), ...]
        """
        for valve_number, state in states:
            self._validate_channel(valve_number)
            self._set_channel_bit(valve_number, state)

        self.apply_state()

    def apply_state(self) -> None:
        self._ensure_ready()
        ok = self._send_packet_and_check(self._state_bytes, label="APPLY STATE")
        if not ok:
            raise BoardProtocolError("Плата вернула некорректный ответ на snapshot-пакет")

    def initialize_board(self) -> None:
        """
        Инициализация платы:
        - открываем порт
        - отправляем стартовую последовательность БЕЗ ожидания ответа
        - отправляем первый рабочий нулевой snapshot
        - ждем стабилизацию
        - чистим входной буфер
        """
        self.open()
        self._run_init_sequence()

        time.sleep(0.05)
        self._send_working_zero_snapshot()

        # Даем плате время спокойно перейти в рабочий режим
        time.sleep(0.1)

        # Чистим мусор/остатки после старта
        if self._ser:
            self._ser.reset_input_buffer()

        self._initialized = True
        print("[INIT] Board initialized")

    def ping(self) -> bool:
        """
        Проверка связи: повторно отправляем текущий snapshot.
        """
        self._ensure_ready()
        return self._send_packet_and_check(self._state_bytes, label="PING")

    # ----------------------------
    # Внутренняя логика
    # ----------------------------
    def _ensure_ready(self) -> None:
        if not self.is_open:
            raise BoardNotConnectedError("COM-порт платы не открыт")

        if not self._initialized:
            raise BoardProtocolError("Плата не инициализирована. Сначала вызови initialize_board()")

    def _validate_channel(self, channel: int) -> None:
        if channel < 1 or channel > self.channels_count:
            raise ValueError(f"Valve number out of range: {channel}")

    def _set_channel_bit(self, channel: int, value: bool) -> None:
        byte_index = (channel - 1) // 8
        bit_index = (channel - 1) % 8

        if value:
            self._state_bytes[byte_index] |= (1 << bit_index)
        else:
            self._state_bytes[byte_index] &= ~(1 << bit_index)

    def _build_main_packet(self, state_bytes: list[int]) -> bytes:
        if len(state_bytes) != self.state_bytes_count:
            raise ValueError(
                f"state_bytes должен содержать ровно {self.state_bytes_count} байт"
            )

        checksum = (0x3D - sum(state_bytes)) & 0xFF
        header = bytes([0xB0, 0x11, 0x01, 0x00])
        return header + bytes(state_bytes) + bytes([checksum])

    def _build_full_packet(self, state_bytes: list[int]) -> bytes:
        return self._build_main_packet(state_bytes) + self.SHORT_PACKET

    def _read_response(self, wait_timeout: float = 0.3, settle_time: float = 0.03) -> bytes:
        """
        Читаем ответ от платы.
        Логика:
        - ждем первые байты
        - как только байты начали идти, собираем их
        - когда линия затихла на settle_time, считаем ответ законченным
        """
        if not self._ser:
            return b""

        start_time = time.time()
        data = bytearray()
        last_rx_time = None

        while time.time() - start_time < wait_timeout:
            waiting = self._ser.in_waiting
            if waiting > 0:
                chunk = self._ser.read(waiting)
                if chunk:
                    data.extend(chunk)
                    last_rx_time = time.time()

            if last_rx_time is not None and (time.time() - last_rx_time) >= settle_time:
                break

            time.sleep(0.002)

        return bytes(data)

    def _send_packet_and_check(self, state_bytes: list[int], label: str = "") -> bool:
        if not self._ser:
            raise BoardNotConnectedError("COM-порт платы не открыт")

        tx_packet = self._build_full_packet(state_bytes)

        # Перед рабочей командой очищаем хвосты старых ответов
        self._ser.reset_input_buffer()

        self._ser.write(tx_packet)
        self._ser.flush()

        rx_packet = self._read_response()

        print(f"[BOARD] {label} TX: {tx_packet.hex(' ').upper()}")

        if not rx_packet:
            print(f"[BOARD] {label}: нет ответа от платы")
            return False

        print(f"[BOARD] {label} RX: {rx_packet.hex(' ').upper()}")

        ack = self.EXPECTED_ACK

        # 1. Идеальный случай: echo + ack
        if rx_packet == tx_packet + ack:
            print(f"[BOARD] {label}: OK (echo + ack)")
            return True

        # 2. Только ACK
        if rx_packet == ack:
            print(f"[BOARD] {label}: OK (ack only)")
            return True

        # 3. Наш tx где-то внутри + ответ заканчивается ACK
        if rx_packet.endswith(ack) and tx_packet in rx_packet:
            print(f"[BOARD] {label}: OK (tx found + ack at end)")
            return True

        # 4. Просто ACK где-то внутри
        if ack in rx_packet:
            print(f"[BOARD] {label}: OK (ack found in response)")
            return True

        print(f"[BOARD] {label}: ответ не распознан")
        return False

    # ----------------------------
    # Инициализация платы
    # ----------------------------
    @staticmethod
    def _hx(s: str) -> bytes:
        return bytes.fromhex(s)

    @staticmethod
    def _sleep_precise(delay_s: float) -> None:
        if delay_s <= 0:
            return

        end = time.perf_counter() + delay_s

        if delay_s > 0.002:
            time.sleep(delay_s - 0.001)

        while time.perf_counter() < end:
            pass

    def _send_chunk(self, data_hex: str, label: str = "") -> None:
        if not self._ser:
            raise BoardNotConnectedError("COM-порт платы не открыт")

        data = self._hx(data_hex)
        self._ser.write(data)
        self._ser.flush()

        if label:
            print(f"[INIT] {label:<12} {data_hex}")
        else:
            print(f"[INIT] {data_hex}")

    def _run_init_sequence(self) -> None:
        """
        Стартовая последовательность.
        Здесь ОТВЕТЫ НЕ ЖДЕМ.
        Просто строго отправляем нужные кадры и выдерживаем паузы.
        """
        sequence = [
            ("85 04 00 76", 0.009940833, "start_1"),
            ("84 04 00 77", 0.009934458, "start_2"),
            ("80 04 01 7A", 0.010246417, "start_3"),
            ("86 04 01 74", 0.000552958, "start_4"),
            ("B1 08 01 00 02 70 00 D3", 1.199265708, "start_5"),

            ("B1 08 01 00 02 06 00 3D", 0.001131250, "cfg_06"),
            ("B1 08 01 00 02 20 FF 24", 0.001132750, "cfg_20"),
            ("B1 08 01 00 02 21 D3 4F", 0.001131167, "cfg_21"),
            ("B1 08 01 00 02 22 B5 6C", 0.001132833, "cfg_22"),
            ("B1 08 01 00 02 23 97 89", 0.001132792, "cfg_23"),
            ("B1 08 01 00 02 24 79 A6", 0.001131292, "cfg_24"),
            ("B1 08 01 00 02 25 5B C3", 0.001132833, "cfg_25"),
            ("B1 08 01 00 02 26 00 1D", 0.001132792, "cfg_26"),
            ("B1 08 01 00 02 49 00 FA", 0.001132875, "cfg_49"),
            ("B1 08 01 00 02 40 00 03", 0.003085292, "cfg_40"),

            ("B1 08 01 00 0A 83 00 B8", 0.000302375, "blk1_b1"),
            ("B2 08 01 02 0B 83 00 B4", 0.001095042, "blk1_b2"),
            ("B3 04 01 47",             0.009791958, "blk1_b3"),

            ("B1 08 01 00 12 83 00 B0", 0.000302292, "blk2_b1"),
            ("B2 08 01 02 13 83 00 AC", 0.001095000, "blk2_b2"),
            ("B3 04 01 47",             0.010296458, "blk2_b3"),

            ("B1 08 01 00 1A 83 00 A8", 0.000302417, "blk3_b1"),
            ("B2 08 01 02 1B 83 00 A4", 0.001095083, "blk3_b2"),
            ("B3 04 01 47",             0.010298208, "blk3_b3"),

            ("B1 08 01 00 22 83 00 A0", 0.000302333, "blk4_b1"),
            ("B2 08 01 02 23 83 00 9C", 0.001094958, "blk4_b2"),
            ("B3 04 01 47",             0.010297917, "blk4_b3"),

            ("B1 08 01 00 2A 83 00 98", 0.000300792, "blk5_b1"),
            ("B2 08 01 02 2B 83 00 94", 0.001096583, "blk5_b2"),
            ("B3 04 01 47",             0.010296250, "blk5_b3"),

            ("B1 08 01 00 32 83 00 90", 0.000302333, "blk6_b1"),
            ("B2 08 01 02 33 83 00 8C", 0.001095000, "blk6_b2"),
            ("B3 04 01 47",             0.010385917, "blk6_b3"),

            ("B0 11 01 00 00 00 00 00 00 00 00 00 00 00 00 00 3D", 0.0, "zero_snapshot"),
        ]

        print("[INIT] === INIT SEQUENCE START ===")
        for data_hex, delay_after, label in sequence:
            self._send_chunk(data_hex, label)
            if delay_after > 0:
                self._sleep_precise(delay_after)
        print("[INIT] === INIT SEQUENCE DONE ===")

    def _send_working_zero_snapshot(self) -> None:
        """
        После init отправляем первый рабочий snapshot:
        сначала main packet, потом через ~3.93 ms хвост.
        Ответ тут тоже специально не ждем.
        """
        if not self._ser:
            raise BoardNotConnectedError("COM-порт платы не открыт")

        part1 = self._build_main_packet(self._state_bytes)
        part2 = self.SHORT_PACKET

        print("[INIT] === WORKING ZERO SNAPSHOT START ===")
        self._ser.write(part1)
        self._ser.flush()

        self._sleep_precise(0.00393)

        self._ser.write(part2)
        self._ser.flush()
        print("[INIT] === WORKING ZERO SNAPSHOT DONE ===")