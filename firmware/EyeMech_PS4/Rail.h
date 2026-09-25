#pragma once
// 5 V rail monitor (Scott, 2026-09-25): is the servo supply sagging? A 10k/10k divider from
// the ESP32's 5 V pin to GPIO34 (ADC1, so it works with Wi-Fi on) and GND. A core-0 task
// samples in bursts of 16 every tick, ~16k samples/s, so millisecond servo dips are caught.
// ESP32 ADC accuracy is ~±0.1 V: good for dips of half a volt, not for absolute calibration.
#include <Arduino.h>

void railBegin();
int railNowMv();      // average of the latest burst; < 1000 = divider not wired
int railMinMv();      // lowest single sample since boot or railReset()
int railMaxMv();
uint32_t railDips();  // times the rail went below RAIL_DIP_MV (with 100 mV hysteresis)
void railReset();
const char *resetReasonName();  // why the chip last restarted: "brownout" is the one to watch
static const int RAIL_DIP_MV = 4600;
