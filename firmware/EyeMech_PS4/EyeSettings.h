#pragma once
// The values the web page changes. Changes apply live (a restart would drop the
// controller); Save writes them to NVS namespace "eyes" so they survive power-up.
// Every field is listed once in SETTINGS[] (EyeSettings.cpp) with its range and
// default; the NVS key and the web key are the field name.
#include <Arduino.h>

struct EyeSettings {
  // Rest position, offsets from mechanical centre in the kit's 0..1023 units
  int parkY;         // eyes rest this far below centre, 0..300
  int parkX;         // eyes rest this far right (+) / left (-), -150..150
  // Lids
  int bootTrim;      // lid trim at power-up, -40 (most closed) .. 40 (fully open)
  int lidMin;        // upper lid open limit, 280 (kit) .. 200; Scott's original used 250
  int lowLidMax;     // lower lid open limit, 400 (kit) .. 480
  int lidFollow;     // % the lids follow the eyes up/down, 0..100 (100 = kit)
  // Controller
  int blinkBtn;      // 0 Cross, 1 Square, 2 either
  int trimStep;      // D-pad lid trim per press, 1..20
  // Alive idle
  int idleMode;      // 0 off, 1 automatic, 2 manual only
  int autoIdleSecs;  // unattended this long -> automatic idle, 5..600
  int idleRunMins;   // a manual start runs this long, 0 = until stopped, 0..120
  int glanceTenths;  // mean time between glances, tenths of a second, 5..50
  int glanceRange;   // how far glances go, % of full travel, 10..100
  int blinkRate;     // idle blinks per minute, 0..30
  // Radar (Home Assistant calls /presence)
  int arriveAction;  // 0 nothing, 1 idle, 2 play recording then idle
  int emptyAction;   // 0 keep going, 1 rest, 2 sleep (lids closed)
  int emptyMins;     // bench empty this long -> emptyAction, 1..60
};

extern EyeSettings settings;

// Where the eyes rest with the stick centred, in the kit's 0..1023 units.
inline int restX() { return 512 + settings.parkX; }
inline int restY() { return 512 - settings.parkY; }

void resetSettings(EyeSettings &s);  // every field to its default
void loadSettings();                 // NVS -> settings (defaults where absent)
bool saveSettings();                 // settings -> NVS
bool settingsDirty();                // RAM differs from what NVS holds
bool setSetting(const String &key, int value);  // clamps; false = unknown key
String settingsJson();
