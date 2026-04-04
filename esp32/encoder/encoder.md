#include <Arduino.h>

constexpr int PIN_A   = 18;
constexpr int PIN_B   = 19;
constexpr int PIN_Z   = 21;
constexpr int PIN_RPM = 22;   // индукционный датчик через оптопару

constexpr int ENCODER_PULSES_PER_REV = 1000;
constexpr int RPM_SENSOR_PULSES_PER_REV = 1;

constexpr unsigned long SEND_INTERVAL_MS = 100;
constexpr float MAX_VALID_RPM            = 90.0f;

// Защита от мусорных слишком частых импульсов датчика
constexpr unsigned long RPM_MIN_PULSE_INTERVAL_US = 300000UL;

// Минимальный timeout, если обороты уже были
constexpr unsigned long RPM_MIN_TIMEOUT_US = 3000000UL;   // 3 сек

// Максимальный timeout, чтобы не ждать бесконечно
constexpr unsigned long RPM_MAX_TIMEOUT_US = 15000000UL;  // 15 сек

// Сколько последних периодов усредняем
constexpr int RPM_AVG_SAMPLES = 4;

volatile long encoderCount = 0;
volatile bool zPulseFlag = false;
volatile unsigned long lastZMicros = 0;
volatile unsigned long zPeriodMicros = 0;

// Для индукционного датчика
volatile unsigned long lastRpmPulseMicros = 0;
volatile unsigned long rpmPeriods[RPM_AVG_SAMPLES] = {0};
volatile int rpmPeriodIndex = 0;
volatile int rpmPeriodCount = 0;

// Новый флаг: был реальный импульс полного оборота
volatile bool turnPulseFlag = false;

unsigned long lastSendMs = 0;

int lastAngle = -1;
int lastRpm10 = -1;
int lastT = -1;

void IRAM_ATTR isrA() {
  bool a = digitalRead(PIN_A);
  bool b = digitalRead(PIN_B);

  if (a == b) {
    encoderCount++;
  } else {
    encoderCount--;
  }
}

void IRAM_ATTR isrZ() {
  unsigned long now = micros();

  if (lastZMicros != 0) {
    zPeriodMicros = now - lastZMicros;
  }

  lastZMicros = now;
  encoderCount = 0;
  zPulseFlag = true;
}

void IRAM_ATTR isrRpmSensor() {
  unsigned long now = micros();

  if (lastRpmPulseMicros != 0) {
    unsigned long dt = now - lastRpmPulseMicros;

    if (dt < RPM_MIN_PULSE_INTERVAL_US) {
      return;
    }

    rpmPeriods[rpmPeriodIndex] = dt;
    rpmPeriodIndex++;
    if (rpmPeriodIndex >= RPM_AVG_SAMPLES) {
      rpmPeriodIndex = 0;
    }

    if (rpmPeriodCount < RPM_AVG_SAMPLES) {
      rpmPeriodCount++;
    }
  }

  lastRpmPulseMicros = now;
  turnPulseFlag = true;
}

int getAngleFromCount(long count) {
  long mod = count % ENCODER_PULSES_PER_REV;
  if (mod < 0) {
    mod += ENCODER_PULSES_PER_REV;
  }

  int angle = (mod * 360L) / ENCODER_PULSES_PER_REV;

  if (angle >= 360) {
    angle = 0;
  }

  return angle;
}

float getRpmFromPeriod(unsigned long periodUs) {
  if (periodUs == 0) {
    return 0.0f;
  }

  float pulsesPerMinute = 60000000.0f / (float)periodUs;
  return pulsesPerMinute / (float)RPM_SENSOR_PULSES_PER_REV;
}

unsigned long getAverageRpmPeriod() {
  noInterrupts();
  int count = rpmPeriodCount;
  unsigned long localPeriods[RPM_AVG_SAMPLES];
  for (int i = 0; i < RPM_AVG_SAMPLES; i++) {
    localPeriods[i] = rpmPeriods[i];
  }
  interrupts();

  if (count == 0) {
    return 0;
  }

  unsigned long sum = 0;
  for (int i = 0; i < count; i++) {
    sum += localPeriods[i];
  }

  return sum / (unsigned long)count;
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_A, INPUT_PULLUP);
  pinMode(PIN_B, INPUT_PULLUP);
  pinMode(PIN_Z, INPUT_PULLUP);
  pinMode(PIN_RPM, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(PIN_A), isrA, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_Z), isrZ, FALLING);

  // Оставляем тот фронт, на котором у тебя реально работает
  attachInterrupt(digitalPinToInterrupt(PIN_RPM), isrRpmSensor, RISING);

  delay(200);
}

void loop() {
  unsigned long nowMs = millis();

  if (nowMs - lastSendMs < SEND_INTERVAL_MS) {
    return;
  }
  lastSendMs = nowMs;

  noInterrupts();
  long count = encoderCount;
  bool z = zPulseFlag;
  zPulseFlag = false;

  bool turnPulse = turnPulseFlag;
  turnPulseFlag = false;

  unsigned long lastRpmPulse = lastRpmPulseMicros;
  interrupts();

  unsigned long avgPeriod = getAverageRpmPeriod();
  float rpm = getRpmFromPeriod(avgPeriod);

  unsigned long rpmTimeoutUs = RPM_MAX_TIMEOUT_US;

  if (avgPeriod > 0) {
    rpmTimeoutUs = avgPeriod * 25UL / 10UL; // 2.5 * period

    if (rpmTimeoutUs < RPM_MIN_TIMEOUT_US) {
      rpmTimeoutUs = RPM_MIN_TIMEOUT_US;
    }
    if (rpmTimeoutUs > RPM_MAX_TIMEOUT_US) {
      rpmTimeoutUs = RPM_MAX_TIMEOUT_US;
    }
  }

  if (lastRpmPulse == 0 || (micros() - lastRpmPulse > rpmTimeoutUs)) {
    rpm = 0.0f;
  }

  if (rpm > MAX_VALID_RPM) {
    rpm = 0.0f;
  }

  int angle = z ? 0 : getAngleFromCount(count);
  int rpm10 = (int)(rpm * 10.0f + 0.5f);
  int tInt = turnPulse ? 1 : 0;

  if (angle != lastAngle || z || rpm10 != lastRpm10 || tInt != lastT) {
    Serial.print("A:");
    Serial.print(angle);
    Serial.print(" R:");
    Serial.print(rpm, 1);
    Serial.print(" Z:");
    Serial.print(z ? 1 : 0);
    Serial.print(" T:");
    Serial.print(turnPulse ? 1 : 0);
    Serial.println();

    lastAngle = angle;
    lastRpm10 = rpm10;
    lastT = tInt;
  }
}