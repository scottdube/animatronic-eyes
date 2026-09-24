#include "EyeSettings.h"
#include <Preferences.h>
#include <stddef.h>

EyeSettings settings;
static EyeSettings saved;  // what NVS holds, for settingsDirty()

static const char *NS = "eyes";

struct Field {
  const char *key;  // NVS key (max 15 chars) and web key
  size_t offset;
  int lo, hi, def;
};

#define F(name, lo, hi, def) {#name, offsetof(EyeSettings, name), lo, hi, def}
static const Field SETTINGS[] = {
    F(parkY, 0, 300, 180),        F(parkX, -150, 150, 0),
    F(bootTrim, -40, 40, 40),     F(lidMin, 200, 280, 280),
    F(lidFollow, 0, 100, 100),    F(blinkBtn, 0, 2, 0),
    F(trimStep, 1, 20, 5),        F(idleMode, 0, 2, 1),
    F(autoIdleSecs, 5, 600, 20),  F(idleRunMins, 0, 120, 5),
    F(glanceTenths, 5, 50, 20),   F(glanceRange, 10, 100, 60),
    F(blinkRate, 0, 30, 12),      F(arriveAction, 0, 2, 1),
    F(emptyAction, 0, 2, 2),      F(emptyMins, 1, 60, 5),
};
#undef F
static const size_t N = sizeof SETTINGS / sizeof SETTINGS[0];

static int &ref(EyeSettings &s, const Field &f) { return *(int *)((char *)&s + f.offset); }

void resetSettings(EyeSettings &s) {
  for (size_t i = 0; i < N; i++) ref(s, SETTINGS[i]) = SETTINGS[i].def;
}

void loadSettings() {
  EyeSettings d;
  resetSettings(d);
  Preferences p;
  if (p.begin(NS, true)) {  // fails when the namespace doesn't exist yet: defaults stand
    for (size_t i = 0; i < N; i++) {
      const Field &f = SETTINGS[i];
      ref(d, f) = constrain(p.getInt(f.key, f.def), f.lo, f.hi);
    }
    p.end();
  }
  settings = d;
  saved = d;
}

bool saveSettings() {
  Preferences p;
  if (!p.begin(NS, false)) return false;
  bool ok = true;
  for (size_t i = 0; i < N; i++) {
    const Field &f = SETTINGS[i];
    // putInt returns bytes written: 0 = failed. Skip unchanged keys to spare flash.
    if (p.getInt(f.key, f.def - 1) != ref(settings, f) || !p.isKey(f.key))
      ok = p.putInt(f.key, ref(settings, f)) && ok;
  }
  p.end();
  if (ok) saved = settings;
  return ok;
}

bool settingsDirty() { return memcmp(&saved, &settings, sizeof settings) != 0; }

bool setSetting(const String &key, int v) {
  for (size_t i = 0; i < N; i++) {
    const Field &f = SETTINGS[i];
    if (key == f.key) {
      ref(settings, f) = constrain(v, f.lo, f.hi);
      return true;
    }
  }
  return false;
}

String settingsJson() {
  String s = "{";
  for (size_t i = 0; i < N; i++) {
    s += '"';
    s += SETTINGS[i].key;
    s += "\":";
    s += ref(settings, SETTINGS[i]);
    s += ',';
  }
  s += "\"dirty\":";
  s += settingsDirty() ? "true" : "false";
  s += '}';
  return s;
}
