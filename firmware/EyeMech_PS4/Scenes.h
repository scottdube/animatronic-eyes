#pragma once
// Who drives the eyes: controller > playback > alive idle > rest (sleep = rest
// with the lids held closed). Every source produces a Frame, the same thing
// the controller produces, and the sketch runs the kit's servo math on it.
// Spec: docs/superpowers/specs/2026-09-24-eyemech-scenes-design.md
#include <Arduino.h>

struct Frame {
  int sx, sy;   // stick space, -128..127, 0 = rest position
  bool blink;
  int lid;      // lids % open, 0 = closed .. 100 = wide (EyeSettings lid presets)
  bool limp = false;  // stop the servo pulses (quiet sleep)
  int wink = 0;       // one eye closed: 0 none, 1 his left, 2 his right (his own left/right)
};

struct PadState {
  bool connected;
  bool takeover;   // a stick past the deadzone, the blink button(s) or the D-pad
  bool triangle, circle, share;  // scene commands (edges are detected in Scenes)
};

enum SceneMode { M_REST, M_LIVE, M_IDLE, M_PLAY, M_RECORD, M_SLEEP };

void scenesBegin();
void scenesBoot();  // after settings load: power-up counts as an arrival
// Once per loop. `live` is what the controller says (or rest when disconnected).
Frame scenesUpdate(const PadState &pad, const Frame &live, uint32_t now);

SceneMode sceneMode();
const char *sceneModeName();   // "live", "idle", ... for /status
// From the web page / Home Assistant: show (= idle) | extended | play | record | stop | sleep | wake
bool sceneCommand(const String &cmd);
void scenePresence(bool present);  // from Home Assistant via /presence
bool scenePresent();
int sceneNextShowSecs();           // to the next show the eyes start on their own, -1 = none
int sceneShowLeftSecs();           // left in the running show, -1 = none
uint32_t recordingMs();            // length of the stored recording, 0 = none
