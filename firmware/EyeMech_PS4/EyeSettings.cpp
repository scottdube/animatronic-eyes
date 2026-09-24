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
    F(lidWide, 0, 100, 100),      F(lidNormal, 0, 100, 75),
    F(lidSquint, 0, 100, 35),     F(lidClosed, 0, 100, 0),
    F(lowLidCurve, 25, 300, 50),
    F(lidMin, 160, 280, 280),
    F(lowLidMax, 400, 520, 400),  F(lidFollow, 0, 100, 100),
    F(cTopL, -60, 60, 0), F(cBotL, -60, 60, 0), F(cTopR, -60, 60, 0), F(cBotR, -60, 60, 0),
    F(sTopL, -60, 60, 0), F(sBotL, -60, 60, 0), F(sTopR, -60, 60, 0), F(sBotR, -60, 60, 0),
    F(nTopL, -60, 60, 0), F(nBotL, -60, 60, 0), F(nTopR, -60, 60, 0), F(nBotR, -60, 60, 0),
    F(wTopL, -60, 60, 0), F(wBotL, -60, 60, 0), F(wTopR, -60, 60, 0), F(wBotR, -60, 60, 0),
    F(blinkBtn, 0, 2, 0),
    F(idleMode, 0, 2, 1),
    F(autoIdleSecs, 5, 600, 20),  F(idleRunMins, 0, 120, 5),
    F(glanceTenths, 5, 50, 20),   F(glanceRange, 10, 100, 60),
    F(blinkRate, 0, 30, 12),      F(arriveAction, 0, 2, 1),
    F(emptyAction, 0, 2, 2),      F(emptyMins, 1, 60, 5),
};
#undef F
static_assert(offsetof(EyeSettings, wBotR) - offsetof(EyeSettings, cTopL) == 15 * sizeof(int),
              "lidTrim() indexes the 16 trims as one array");
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
