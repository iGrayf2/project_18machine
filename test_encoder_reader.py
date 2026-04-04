import serial
import time


PORT = "COM6"
BAUDRATE = 115200


def main():
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)

    print(f"Listening {PORT} ...")

    # ESP32 часто перезагружается при открытии порта
    time.sleep(2)

    # Чистим стартовый мусор после загрузчика
    ser.reset_input_buffer()

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            print(line)

    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        ser.close()


if __name__ == "__main__":
    main()