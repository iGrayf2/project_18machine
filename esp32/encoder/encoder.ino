#include <Arduino.h>

constexpr int PIN_A = 18;
constexpr int PIN_B = 19;
constexpr int PIN_Z = 21;

constexpr int PULSES_PER_REV = 1000;   // 1000 PPR
constexpr unsigned long SEND_INTERVAL_MS = 20;

volatile long encoderCount = 0;
volatile bool zPulseFlag = false;
volatile unsigned long lastZMicros = 0;
volatile unsigned long zPeriodMicros = 0;

unsigned long lastSendMs = 0;
int lastAngle = 0;
float lastRpm = 0.0f;

void IRAM_ATTR isrA() {
  // Если после оптопары сигнал инвертирован,
  // то условие направления может потребовать смены знака.
  bool aState = digitalRead(PIN_A);
  bool bState = digitalRead(PIN_B);

  // Счет по фронтам A с учетом B
  if (aState == bState) {
    encoderCount++;
  } else {
    encoderCount--;
  }
}

void IRAM_ATTR isrZ() {
  unsigned long now = micros();
  zPeriodMicros = now - lastZMicros;
  lastZMicros = now;

  encoderCount = 0;
  zPulseFlag = true;
}

int normalizeAngle(long count) {
  long mod = count % PULSES_PER_REV;
  if (mod < 0) {
    mod += PULSES_PER_REV;
  }

  int angle = (mod * 360L) / PULSES_PER_REV;

  if (angle >= 360) {
    angle = 0;
  }

  return angle;
}

float calculateRpm(unsigned long periodMicros) {
  if (periodMicros == 0) {
    return 0.0f;
  }

  return 60000000.0f / (float)periodMicros;
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_A, INPUT_PULLUP);
  pinMode(PIN_B, INPUT_PULLUP);
  pinMode(PIN_Z, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(PIN_A), isrA, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_Z), isrZ, FALLING);

  delay(500);
  Serial.println("ENCODER_START");
}

void loop() {
  unsigned long nowMs = millis();

  if (nowMs - lastSendMs >= SEND_INTERVAL_MS) {
    lastSendMs = nowMs;

    noInterrupts();
    long countCopy = encoderCount;
    bool zCopy = zPulseFlag;
    unsigned long zPeriodCopy = zPeriodMicros;
    zPulseFlag = false;
    interrupts();

    int angle = normalizeAngle(countCopy);
    float rpm = calculateRpm(zPeriodCopy);

    // Если Z давно не было, считаем что RPM = 0
    if (micros() - lastZMicros > 2000000UL) {
      rpm = 0.0f;
    }

    lastAngle = angle;
    lastRpm = rpm;

    Serial.print("ANGLE:");
    Serial.print(angle);
    Serial.print(",RPM:");
    Serial.print(rpm, 1);
    Serial.print(",TURN:");
    Serial.print(zCopy ? 1 : 0);
    Serial.print(",COUNT:");
    Serial.println(countCopy);
  }
}