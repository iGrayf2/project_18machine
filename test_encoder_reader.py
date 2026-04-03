import serial


PORT = "COM6"      # поставь свой порт ESP32
BAUDRATE = 115200


def main():
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)

    print(f"Listening {PORT} ...")
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