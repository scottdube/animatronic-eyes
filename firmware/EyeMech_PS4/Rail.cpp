#include "Rail.h"
#include <esp_system.h>

static const int PIN = 34;
static const int DIVIDER = 2;  // 10k over 10k
static volatile int nowMv = 0, minMv = 99999, maxMv = 0;
static volatile uint32_t dips = 0;
static volatile bool resetReq = true;  // the first burst starts the stats clean

// Stats are on burst AVERAGES (16 samples, ~1 ms), not single samples: measured
// 2026-09-25, single samples spread 3.9..4.77 V on a flat 4.47 V rail with the servos
// asleep and drawing nothing, so a single-sample min is ADC noise. A dip is relative to the
// rail's own running level (the USB-fed 5 V pin sits ~4.47 V behind the board's diode;
// a direct feed sits nearer 5.0), so one threshold serves both supplies.
static volatile int levelMv = 0;

static void railTask(void *) {
  bool below = false;
  float ema = 0;
  for (;;) {
    long sum = 0;
    for (int i = 0; i < 16; i++) sum += analogReadMilliVolts(PIN) * DIVIDER;
    int avg = sum / 16;
    nowMv = avg;
    if (resetReq || ema == 0) ema = avg;
    ema += (avg - ema) * 0.0005f;  // ~2 s at ~1 burst per ms: the rail's own level
    levelMv = (int)ema;
    if (resetReq) {
      resetReq = false;
      minMv = 99999;
      maxMv = 0;
      dips = 0;
      below = false;
    }
    if (avg < minMv) minMv = avg;
    if (avg > maxMv) maxMv = avg;
    if (avg < ema - RAIL_DIP_MV) {
      if (!below) dips++;
      below = true;
    } else if (avg > ema - RAIL_DIP_MV + 100) {
      below = false;
    }
    vTaskDelay(1);  // lets the idle task run (watchdog), ~1 ms
  }
}

void railBegin() {
  analogSetPinAttenuation(PIN, ADC_11db);  // ~0.15..3.1 V: 2.5 V at a 5 V rail
  // Core 0 at priority 1: only spare time there (Wi-Fi and Bluetooth run above it); the
  // servo loop on core 1 is untouched.
  xTaskCreatePinnedToCore(railTask, "rail", 3072, nullptr, 1, nullptr, 0);
}

int railNowMv() { return nowMv; }
int railMinMv() { return minMv == 99999 ? 0 : minMv; }
int railMaxMv() { return maxMv; }
int railLevelMv() { return levelMv; }
uint32_t railDips() { return dips; }
void railReset() { resetReq = true; }

const char *resetReasonName() {
  switch (esp_reset_reason()) {
    case ESP_RST_POWERON: return "power-on";
    case ESP_RST_BROWNOUT: return "brownout";
    case ESP_RST_SW: return "software";  // OTA, or a restart the sketch asked for
    case ESP_RST_PANIC: return "crash";
    case ESP_RST_INT_WDT:
    case ESP_RST_TASK_WDT:
    case ESP_RST_WDT: return "watchdog";
    case ESP_RST_EXT: return "reset pin";
    case ESP_RST_DEEPSLEEP: return "deep sleep";
    default: return "unknown";
  }
}
