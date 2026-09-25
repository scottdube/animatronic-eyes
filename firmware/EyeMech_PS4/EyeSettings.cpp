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
    F(xCenter, -40, 40, 0),
    F(lidWide, 0, 100, 100),      F(lidNormal, 0, 100, 75),
    F(lidSquint, 0, 100, 35),     F(lidClosed, 0, 100, 0),
    F(lowLidCurve, 25, 300, 50),
    F(lidMin, 160, 280, 280),
    F(lowLidMax, 400, 520, 400),  F(lidFollow, 0, 100, 100),
    F(cLTop, -60, 60, 0), F(cLBot, -60, 60, 0), F(cRTop, -60, 60, 0), F(cRBot, -60, 60, 0),
    F(sLTop, -60, 60, 0), F(sLBot, -60, 60, 0), F(sRTop, -60, 60, 0), F(sRBot, -60, 60, 0),
    F(nLTop, -60, 60, 0), F(nLBot, -60, 60, 0), F(nRTop, -60, 60, 0), F(nRBot, -60, 60, 0),
    F(wLTop, -60, 60, 0), F(wLBot, -60, 60, 0), F(wRTop, -60, 60, 0), F(wRBot, -60, 60, 0),
    F(blinkBtn, 0, 2, 0),
    F(idleMode, 0, 2, 1),
    F(arriveDelay, 0, 300, 30),   F(showSecs, 30, 900, 150),
    F(showEvery, 0, 240, 60),     F(extendMins, 1, 120, 20),
    F(handsOffSecs, 5, 600, 20),  F(sleepQuiet, 0, 1, 1),
    F(glanceTenths, 5, 50, 20),   F(glanceRange, 10, 100, 60),
    F(blinkRate, 0, 30, 12),      F(arriveAction, 0, 2, 1),
    F(emptyMins, 1, 60, 5),
};
#undef F
static_assert(offsetof(EyeSettings, wRBot) - offsetof(EyeSettings, cLTop) == 15 * sizeof(int),
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
  bool migrate = false, xMigrate = false;
  if (p.begin(NS, true)) {  // fails when the namespace doesn't exist yet: defaults stand
    for (size_t i = 0; i < N; i++) {
      const Field &f = SETTINGS[i];
      ref(d, f) = constrain(p.getInt(f.key, f.def), f.lo, f.hi);
    }
    // Until 2026-09-25 the trims were named as seen FACING him (cTopL = the eye on your
    // left = his right). Carry them over to his own left/right once, then drop the old keys.
    migrate = !p.isKey("cLTop") && p.isKey("cTopL");
    // Until 2026-09-25 the pupil center carried the servo's calibration (parkX -75 = true
    // center). Move it into xCenter, in pulse counts (the kit maps 1023 units to 220), so
    // parkX reads 0 there. Same rest position, and the travel becomes even about it.
    if (!p.isKey("xCenter") && d.parkX) {
      d.xCenter = constrain((int)lroundf(d.parkX * 220.0f / 1023), -40, 40);
      d.parkX = 0;
      xMigrate = true;
    }
    if (migrate)
      for (int k = 0; k < 16; k++) {
        const char *pre = "cccc" "ssss" "nnnn" "wwww";
        static const char *oldLid[4] = {"TopR", "BotR", "TopL", "BotL"};  // his LTop, LBot, RTop, RBot
        String key = String(pre[k]) + oldLid[k % 4];
        (&d.cLTop)[k] = constrain(p.getInt(key.c_str(), 0), -60, 60);
      }
    p.end();
  }
  settings = d;
  saved = d;
  if (xMigrate && !migrate && saveSettings()) Serial.println("Settings: pupil center moved into xCenter");
  if (migrate && saveSettings() && p.begin(NS, false)) {
    for (const char *pre : {"c", "s", "n", "w"})
      for (const char *lid : {"TopL", "BotL", "TopR", "BotR"}) p.remove((String(pre) + lid).c_str());
    p.end();
    Serial.println("Settings: lid trims moved to his own left/right");
  }
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
