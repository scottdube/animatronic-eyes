#include "EyeSettings.h"
#include <Preferences.h>

EyeSettings settings;
static EyeSettings saved;  // what NVS holds, for settingsDirty()

static const char *NS = "eyes";

bool clampSettings(EyeSettings &s) {
  EyeSettings before = s;
  s.parkY = constrain(s.parkY, 0, 300);
  s.parkX = constrain(s.parkX, -150, 150);
  s.bootTrim = constrain(s.bootTrim, -40, 40);
  s.blinkBtn = constrain(s.blinkBtn, 0, 2);
  s.trimStep = constrain(s.trimStep, 1, 20);
  return memcmp(&before, &s, sizeof s) == 0;
}

void loadSettings() {
  Preferences p;
  EyeSettings d;  // defaults
  if (p.begin(NS, true)) {
    d.parkY = p.getInt("parkY", d.parkY);
    d.parkX = p.getInt("parkX", d.parkX);
    d.bootTrim = p.getInt("bootTrim", d.bootTrim);
    d.blinkBtn = p.getInt("blinkBtn", d.blinkBtn);
    d.trimStep = p.getInt("trimStep", d.trimStep);
    p.end();
  }  // a namespace that doesn't exist yet fails read-only begin: defaults stand
  clampSettings(d);
  settings = d;
  saved = d;
}

bool saveSettings() {
  Preferences p;
  if (!p.begin(NS, false)) return false;
  bool ok = p.putInt("parkY", settings.parkY) && p.putInt("parkX", settings.parkX) &&
            p.putInt("bootTrim", settings.bootTrim) && p.putInt("blinkBtn", settings.blinkBtn) &&
            p.putInt("trimStep", settings.trimStep);
  p.end();
  if (ok) saved = settings;
  return ok;
}

bool settingsDirty() { return memcmp(&saved, &settings, sizeof settings) != 0; }

bool setSetting(const String &key, int v) {
  if (key == "parkY") settings.parkY = v;
  else if (key == "parkX") settings.parkX = v;
  else if (key == "bootTrim") settings.bootTrim = v;
  else if (key == "blinkBtn") settings.blinkBtn = v;
  else if (key == "trimStep") settings.trimStep = v;
  else return false;
  clampSettings(settings);
  return true;
}

String settingsJson() {
  char buf[160];
  snprintf(buf, sizeof buf,
           "{\"parkY\":%d,\"parkX\":%d,\"bootTrim\":%d,\"blinkBtn\":%d,\"trimStep\":%d,\"dirty\":%s}",
           settings.parkY, settings.parkX, settings.bootTrim, settings.blinkBtn, settings.trimStep,
           settingsDirty() ? "true" : "false");
  return buf;
}
