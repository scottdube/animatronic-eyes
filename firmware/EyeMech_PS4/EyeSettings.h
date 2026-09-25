#pragma once
// The values the web page changes. Changes apply live (a restart would drop the
// controller); Save writes them to NVS namespace "eyes" so they survive power-up.
// Every field is listed once in SETTINGS[] (EyeSettings.cpp) with its range and
// default; the NVS key and the web key are the field name.
#include <Arduino.h>

struct EyeSettings {
  // Rest position, offsets from mechanical center in the kit's 0..1023 units
  int parkY;         // eyes rest this far below center, 0..300
  int parkX;         // eyes rest this far to HIS left (+) / his right (-), -150..150 (measured 2026-09-25)
  // Calibration: where the left/right servo's true center is, in pulse counts. The horn's
  // spline can't land it (~17 deg a tooth), so it lives here and parkX reads 0 at true center.
  int xCenter;       // + = toward his left, -40..40
  int yCenter;       // up/down servo, + = up, -40..40. Servo 1 only: the lids keep following
                     // the commanded gaze, so their trims stay valid
  // Lids
  // Lid presets, % open: 0 = the closed positions the horns were seated to, 100 = the
  // open limits below. D-pad up/down steps closed < squint < normal < wide; power-up is normal.
  int lidWide, lidNormal, lidSquint, lidClosed;
  int lowLidCurve;   // bottom lid % open = top ^ (this/100): 50 gentle (kit-like), 100 = same as top, 200 ahead
  int lidMin;        // upper lid open limit, 280 (kit) .. 160; Scott's original used 250
  int lowLidMax;     // lower lid open limit, 400 (kit) .. 520
  int lidFollow;     // % the lids follow the eyes up/down, 0..100 (100 = kit)
  // Per-preset, per-lid trims, pulse counts, + = more open whichever way the servo turns.
  // Horns alone can't fit it (one adjustment, ~17° spline steps) and the linkage isn't
  // linear, so each preset gets its own; between presets the trim blends by lid %.
  // Prefix c/s/n/w = closed/squint/normal/wide. L/R = HIS left/right, like up/down
  // (Scott, 2026-09-25): L = servos 2 (top) + 3 (bottom), the eye on your right as you
  // face him; R = servos 4 + 5. Keep these 16 together, in order.
  int cLTop, cLBot, cRTop, cRBot;
  int sLTop, sLBot, sRTop, sRBot;
  int nLTop, nLBot, nRTop, nRBot;
  int wLTop, wLBot, wRTop, wRBot;
  // Controller
  int blinkBtn;      // 0 Cross, 1 Square, 2 either
  // Alive idle and shows. A show is a spell of alive idle that ends in sleep.
  int idleMode;      // 0 off (eyes rest open), 1 automatic (arrival, power-up, every showEvery), 2 on demand only
  int arriveDelay;   // seconds from arrival (or power-up) to the show, 0..300
  int showSecs;      // a show lasts this long, 30..900
  int showEvery;     // minutes between shows while someone is there, 0 = none, 0..240
  int extendMins;    // extended play lasts this long, 1..120
  int handsOffSecs;  // controller let go this long -> back to sleep, 5..600
  int sleepQuiet;    // 1 = stop the servo pulses once the lids are closed (silent), 0 = hold
  int glanceTenths;  // mean time between glances, tenths of a second, 5..50
  int glanceRange;   // how far glances go, % of full travel, 10..100
  int blinkRate;     // idle blinks per minute, 0..30
  // Radar (Home Assistant calls /presence)
  int arriveAction;  // what a show is: 0 nothing, 1 alive idle, 2 play the recording then idle
  int emptyMins;     // lab empty this long before a return counts as a new arrival, 1..60
};

extern EyeSettings settings;

// Trim for preset p (0 closed, 1 squint, 2 normal, 3 wide) and lid l (0 his left top,
// 1 his left bottom, 2 his right top, 3 his right bottom)
inline int lidTrim(int p, int l) { return (&settings.cLTop)[p * 4 + l]; }

// Where the eyes rest with the stick centered, in the kit's 0..1023 units.
inline int restX() { return 512 + settings.parkX; }
inline int restY() { return 512 - settings.parkY; }

void resetSettings(EyeSettings &s);  // every field to its default
void loadSettings();                 // NVS -> settings (defaults where absent)
bool saveSettings();                 // settings -> NVS
bool settingsDirty();                // RAM differs from what NVS holds
bool setSetting(const String &key, int value);  // clamps; false = unknown key
String settingsJson();
