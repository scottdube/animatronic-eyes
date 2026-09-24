#pragma once
// The values the web page changes. Changes apply live (a restart would drop the
// controller); Save writes them to NVS namespace "eyes" so they survive power-up.
#include <Arduino.h>

struct EyeSettings {
  int parkY = 180;    // eyes rest this far below centre, kit units of 0..1023 (0..300)
  int parkX = 0;      // eyes rest this far right of centre (+) or left (-), -150..150
  int bootTrim = 40;  // lid trim at power-up, -40 (most closed) .. 40 (fully open)
  int blinkBtn = 0;   // 0 Cross, 1 Square, 2 either
  int trimStep = 5;   // D-pad lid trim per press, 1..20
};

extern EyeSettings settings;

// Clamp every field into range. Returns false if anything had to change.
bool clampSettings(EyeSettings &s);
void loadSettings();          // NVS -> settings (defaults where absent)
bool saveSettings();          // settings -> NVS
bool settingsDirty();         // RAM differs from what NVS holds
// Set one field by its key (the names above). False = unknown key.
bool setSetting(const String &key, int value);
String settingsJson();
