// PCA9685 bench test: one module, one ESP32, serial only (no Wi-Fi, no Bluetooth).
// Written 2026-09-28 to prove the reflowed "dead" module on a spare ESP32 DevKit, so the
// eyes' D1 and its controller link stay untouched. NOT the eyes firmware on purpose: that
// sketch adopts the old DevKit's base MAC and would take .211 and the controller.
//
// Wiring: module VCC -> 3V3, GND -> GND, SDA -> GPIO21, SCL -> GPIO22, module OE -> GND.
// V+ is not needed to scope the outputs.
//
// Serial 115200. On boot: I2C scan, set the chip up at 60 Hz, ch 0-5 PULSING 1.5 ms, dump.
// Needs no serial at all: power it and scope a PWM pin. Keys below are optional.
//   h = ch 0-5 full-on (steady 3.3 V, meter)   l = full-off (0 V)
//   p = 1.5 ms pulses at 60 Hz (scope)          d = dump registers
//   s = I2C scan                                i = set the chip up again
#include <Wire.h>

const uint8_t PRESCALE_60HZ = 101;  // 25 MHz / (4096 * 60) - 1
uint8_t addr = 0x40;

int rd(uint8_t reg) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return -1;
  if (Wire.requestFrom(addr, (uint8_t)1) != 1) return -1;
  return Wire.read();
}

bool wr(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.write(val);
  return Wire.endTransmission() == 0;
}

void scan() {
  Serial.print("I2C scan:");
  int n = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) { Serial.printf(" 0x%02X", a); n++; }
  }
  Serial.println(n ? "" : " nothing answered");
}

bool setup60() {
  if (!wr(0x00, 0x10)) { Serial.printf("no ACK at 0x%02X\n", addr); return false; }  // SLEEP
  wr(0xFE, PRESCALE_60HZ);  // prescale is only writable while asleep
  wr(0x00, 0x20);           // awake, auto-increment
  delay(1);                 // oscillator start-up
  wr(0x01, 0x04);           // MODE2: totem-pole outputs
  return true;
}

void setAll(int t) {  // 1 on, -1 off, 2 pulses
  uint16_t off = t == 2 ? 369 : 0;  // 369/4096 of 16.7 ms = 1.5 ms
  for (uint8_t ch = 0; ch <= 5; ch++) {
    uint8_t b = 0x06 + 4 * ch;  // ON_L, ON_H, OFF_L, OFF_H
    wr(b, 0);
    wr(b + 1, t == 1 ? 0x10 : 0);
    wr(b + 2, off & 0xFF);
    wr(b + 3, t == -1 ? 0x10 : off >> 8);
  }
  Serial.println(t == 1 ? "ch 0-5 HIGH (full-on)" : t == -1 ? "ch 0-5 LOW (full-off)" : "ch 0-5 PULSES 1.5 ms @ 60 Hz");
}

void dump() {
  int pre = rd(0xFE);
  Serial.printf("MODE1 0x%02X  MODE2 0x%02X  prescale %d %s\n", rd(0x00), rd(0x01), pre,
                pre == PRESCALE_60HZ ? "(OK, 60 Hz)" : pre == 254 ? "(254 = BAD readback)" : "(WRONG)");
  for (uint8_t ch = 0; ch <= 5; ch++) {
    uint8_t b = 0x06 + 4 * ch;
    Serial.printf("  ch%u ON %02X %02X  OFF %02X %02X\n", ch, rd(b + 1), rd(b), rd(b + 3), rd(b + 2));
  }
}

// q = probe 0x40 and an empty 0x41 once each: endTransmission code (0 ACK, 2 address NACK,
// 5 timeout, 4 other) and how long the call took. A clean empty bus NACKs in well under 1 ms.
void probe() {
  for (uint8_t a : {(uint8_t)0x40, (uint8_t)0x41}) {
    uint32_t t = micros();
    Wire.beginTransmission(a);
    uint8_t e = Wire.endTransmission();
    Serial.printf("probe 0x%02X: code %u in %lu us\n", a, e, (unsigned long)(micros() - t));
  }
  Serial.printf("pins now: SDA(21)=%d SCL(22)=%d\n", digitalRead(21), digitalRead(22));
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Wire.begin(21, 22);
  Serial.println("\n=== PCA9685 bench test ===");
  probe();
  scan();
  if (setup60()) { setAll(2); dump(); }
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  switch (c) {
    case 'h': setAll(1); dump(); break;
    case 'l': setAll(-1); dump(); break;
    case 'p': setAll(2); dump(); break;
    case 'd': dump(); break;
    case 's': scan(); break;
    case 'q': probe(); break;
    case 'i': if (setup60()) dump(); break;
  }
}
