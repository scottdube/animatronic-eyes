#pragma once
// 5 V rail monitor (Scott, 2026-09-25): is the servo supply sagging? A 10k/10k divider from
// the ESP32's 5 V pin to GPIO34 (ADC1, so it works with Wi-Fi on) and GND. A core-0 task
// samples in bursts of 16 every tick, ~16k samples/s, so millisecond servo dips are caught.
// ESP32 ADC accuracy is ~±0.1 V: good for dips of half a volt, not for absolute calibration.
#include <Arduino.h>

void railBegin();
int railNowMv();      // average of the latest burst; < 1000 = divider not wired
int railMinMv();      // lowest ~1 ms average since boot or railReset()
int railMaxMv();
int railLevelMv();    // the rail's running level (~2 s average)
uint32_t railDips();  // times a ~1 ms average fell RAIL_DIP_MV below the running level
void railReset();
const char *resetReasonName();  // why the chip last restarted: "brownout" is the one to watch
static const int RAIL_DIP_MV = 400;  // a sag this far below the rail's own level; 1 ms averages reach -0.27 V with the servos asleep
