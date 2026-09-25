#include "Rail.h"
#include <esp_system.h>

static const int PIN = 34;
static const int DIVIDER = 2;  // 10k over 10k
static volatile int nowMv = 0, minMv = 99999, maxMv = 0;
static volatile uint32_t dips = 0;
static volatile bool resetReq = true;  // the first burst starts the stats clean

static void railTask(void *) {
  bool below = false;
  for (;;) {
    int lo = 99999, hi = 0;
    long sum = 0;
    for (int i = 0; i < 16; i++) {
      int mv = analogReadMilliVolts(PIN) * DIVIDER;
      sum += mv;
      lo = min(lo, mv);
      hi = max(hi, mv);
    }
    nowMv = sum / 16;
    if (resetReq) {
      resetReq = false;
      minMv = 99999;
      maxMv = 0;
      dips = 0;
      below = false;
    }
    if (lo < minMv) minMv = lo;
    if (hi > maxMv) maxMv = hi;
    if (lo < RAIL_DIP_MV) {
      if (!below) dips++;
      below = true;
    } else if (lo > RAIL_DIP_MV + 100) {
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
