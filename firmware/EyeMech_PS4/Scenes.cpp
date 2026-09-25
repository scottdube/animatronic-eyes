#include "Scenes.h"
#include "EyeSettings.h"
#include <PS4Controller.h>
#include <esp_partition.h>
#include <math.h>

// ---- state ----------------------------------------------------------------
static SceneMode mode = M_REST, shownMode = (SceneMode)-1;
static uint32_t lastActivity = 0;  // takeover or scene command; 0 = boot
static uint32_t lastTakeover = 0;
static bool prevTri = false, prevCir = false, prevShare = false;

static uint32_t idleUntil = 0;  // 0 = runs until stopped
static bool playThenIdle = false;

static bool present = false, emptyPending = false;
// No auto idle until someone is back (controller, arrival, or a page command). Set by a Stop
// (page or Triangle), a timed idle run ending, and the bench going empty with emptyAction=rest.
// Without it a Stop lasted only autoIdleSecs, and a timed run restarted the moment it ended.
static bool holdRest = false;
static bool wasConnected = false;
static uint32_t emptySince = 0;

// ---- alive idle generator --------------------------------------------------
// Gaze is picked in the kit's 0..1023 units as an offset from the rest
// position, NOT in stick units: with the eyes parked low the stick's upper half
// covers ~3x the travel of its lower half, so even stick targets looked up
// most of the time and the pupils disappeared (seen by Scott 2026-09-24).
static const float IDLE_X_MAX = 400, IDLE_Y_MAX = 200;  // offsets at glanceRange 100%
static float gx = 0, gy = 0, tx = 0, ty = 0;
static int idleLid = 75;          // % open; normal, with the odd squint or wide look
static uint32_t idleLidUntil = 0;
static uint32_t nextGlance = 0, nextDrift = 0, nextBlink = 0, blinkEnd = 0, secondBlink = 0;
static uint32_t lastIdleUpdate = 0;

static float frand() { return (float)esp_random() / 4294967295.0f; }  // 0..1

static uint32_t nextBlinkDelay() {
  if (settings.blinkRate <= 0) return 0xFFFFFFFF / 2;
  float mean = 60000.0f / settings.blinkRate;
  float d = -logf(1.0f - frand() * 0.999f) * mean;  // exponential: Poisson blinks
  return (uint32_t)max(800.0f, d);
}

// Inverse of the sketch's stickToAdc (INVERT_X/Y false): an offset from `center`
// in 0..1023 units to the stick value that lands there.
static int adcToStick(float off, int center) {
  float v = off >= 0 ? off * 127.0f / max(1, 1023 - center) : off * 128.0f / max(1, center);
  return constrain((int)lroundf(v), -128, 127);
}

static void idleReset(uint32_t now) {
  tx = ty = 0;
  nextGlance = now + 300;
  nextDrift = now + 400;
  nextBlink = now + nextBlinkDelay();
  blinkEnd = secondBlink = 0;
  idleLidUntil = 0;
  lastIdleUpdate = now;
}

static Frame idleFrame(uint32_t now) {
  if (now >= nextGlance) {
    bool big = frand() < 0.30f;
    float r = settings.glanceRange / 100.0f * (big ? 1.0f : 0.3f);
    tx = (frand() * 2 - 1) * r * IDLE_X_MAX;
    ty = (frand() * 2 - 1) * r * IDLE_Y_MAX;  // people glance sideways more than up/down
    nextGlance = now + (uint32_t)(settings.glanceTenths * 100 * (0.5f + frand()));
    if (big && frand() < 0.25f) nextBlink = now;  // a big glance often comes with a blink
    if (now >= idleLidUntil) {  // now and then a wide look (with a big glance) or a squint
      float r2 = frand();
      if (big && r2 < 0.25f) {
        idleLid = settings.lidWide;
        idleLidUntil = now + 800 + (uint32_t)(frand() * 1200);
      } else if (r2 < 0.10f) {
        idleLid = settings.lidSquint;
        idleLidUntil = now + 1500 + (uint32_t)(frand() * 2500);
      } else {
        idleLid = settings.lidNormal;
      }
    }
  }
  if (now >= nextDrift) {  // small wander between glances
    tx += (frand() * 2 - 1) * 10;
    ty += (frand() * 2 - 1) * 10;
    nextDrift = now + 300 + (uint32_t)(frand() * 400);
  }
  float dt = (float)(now - lastIdleUpdate);
  lastIdleUpdate = now;
  float a = 1.0f - expf(-dt / 60.0f);  // saccade: ~60 ms time constant
  gx += (tx - gx) * a;
  gy += (ty - gy) * a;

  if (now >= nextBlink) {
    blinkEnd = now + 150;
    if (frand() < 0.15f) secondBlink = now + 300;  // double blink
    nextBlink = now + nextBlinkDelay();
  }
  if (secondBlink && now >= secondBlink) {
    blinkEnd = now + 150;
    secondBlink = 0;
  }
  Frame f;
  f.sx = adcToStick(gx, restX());
  f.sy = adcToStick(gy, restY());
  f.blink = now < blinkEnd;
  f.lid = now < idleLidUntil ? idleLid : settings.lidNormal;
  return f;
}

// ---- recording store: the spare 128 KB "spiffs" data partition, raw ----------
// [0..255] header (written last), then 4-byte frames at 50 Hz from offset 256.
static const uint32_t MAGIC = 0x32524559;  // "EYR2": byte 3 is lid % open (EYR1 was trim)
static const uint32_t FRAME_MS = 20, HDR = 256;
struct Header {
  uint32_t magic, frames, frameMs;
};
static const esp_partition_t *part = nullptr;
static uint32_t storedFrames = 0;

static uint8_t wbuf[256];
static size_t wlen = 0;
static uint32_t woff = HDR, recFrames = 0, recNext = 0;

static uint8_t rbuf[256];
static int32_t rbase = -1;
static uint32_t playStart = 0;

static void setLightBar(SceneMode m) {
  if (!PS4.isConnected()) return;
  uint8_t r = 0, g = 0, b = 0, on = 0, off = 0;
  switch (m) {
    case M_IDLE: g = 255; break;
    case M_PLAY: r = 255; b = 255; break;
    case M_RECORD: r = 255; on = off = 25; break;  // flashing, not color alone
    case M_SLEEP: b = 16; break;
    default: b = 255; break;
  }
  PS4.setLed(r, g, b);
  PS4.setFlashRate(on, off);
  PS4.sendToController();
}

static void finishRecording() {
  if (wlen) {
    memset(wbuf + wlen, 0xFF, sizeof wbuf - wlen);
    esp_partition_write(part, woff, wbuf, sizeof wbuf);
    woff += sizeof wbuf;
    wlen = 0;
  }
  Header h = {MAGIC, recFrames, FRAME_MS};
  esp_partition_write(part, 0, &h, sizeof h);  // the header area is still erased
  storedFrames = recFrames;
  Serial.printf("Scene: recorded %lu frames (%.1f s)\n", (unsigned long)recFrames, recFrames * FRAME_MS / 1000.0f);
  mode = M_LIVE;
}

static void stopScene() {
  if (mode == M_RECORD) finishRecording();
  mode = M_REST;
}

static bool startIdle(uint32_t now, bool timed) {
  if (mode == M_RECORD || settings.idleMode == 0) return false;
  idleReset(now);
  idleUntil = (timed && settings.idleRunMins) ? now + settings.idleRunMins * 60000UL : 0;
  mode = M_IDLE;
  return true;
}

static bool startPlay(uint32_t now, bool thenIdle) {
  if (!storedFrames || mode == M_RECORD) return false;
  playThenIdle = thenIdle;
  playStart = now;
  rbase = -1;
  mode = M_PLAY;
  return true;
}

static bool startRecord() {
  if (!part || !PS4.isConnected()) return false;  // a recording is the controller driving
  Serial.println("Scene: erasing recording store");
  esp_partition_erase_range(part, 0, part->size);  // ~1.3 s; the eyes hold still
  storedFrames = 0;
  wlen = 0;
  woff = HDR;
  recFrames = 0;
  recNext = millis();
  mode = M_RECORD;
  return true;
}

static void recordSample(const Frame &f, uint32_t now) {
  if (now - recNext > 200) recNext = now;  // fell behind (e.g. erase): don't burst
  while ((int32_t)(now - recNext) >= 0) {
    recNext += FRAME_MS;
    wbuf[wlen++] = (uint8_t)(int8_t)f.sx;
    wbuf[wlen++] = (uint8_t)(int8_t)f.sy;
    wbuf[wlen++] = f.blink ? 1 : 0;
    wbuf[wlen++] = (uint8_t)f.lid;
    recFrames++;
    if (wlen == sizeof wbuf) {
      esp_partition_write(part, woff, wbuf, sizeof wbuf);
      woff += sizeof wbuf;
      wlen = 0;
      if (woff + sizeof wbuf > part->size) {  // full: ~654 s
        finishRecording();
        return;
      }
    }
  }
}

// Returns false at the end of the recording
static bool playFrame(uint32_t now, Frame &f) {
  uint32_t idx = (now - playStart) / FRAME_MS;
  if (idx >= storedFrames) return false;
  uint32_t off = HDR + idx * 4, base = off & ~255u;
  if ((int32_t)base != rbase) {
    esp_partition_read(part, base, rbuf, sizeof rbuf);
    rbase = base;
  }
  const uint8_t *p = rbuf + (off - base);
  f.sx = (int8_t)p[0];
  f.sy = (int8_t)p[1];
  f.blink = p[2] & 1;
  f.lid = constrain((int)p[3], 0, 100);
  return true;
}

// ---- public -----------------------------------------------------------------
void scenesBegin() {
  part = esp_partition_find_first(ESP_PARTITION_TYPE_DATA, ESP_PARTITION_SUBTYPE_DATA_SPIFFS, nullptr);
  if (!part) {
    Serial.println("Scene: no spiffs partition - recording disabled (flash with PartitionScheme=min_spiffs)");
    return;
  }
  Header h;
  esp_partition_read(part, 0, &h, sizeof h);
  if (h.magic == MAGIC && h.frameMs == FRAME_MS && HDR + h.frames * 4 <= part->size) storedFrames = h.frames;
  Serial.printf("Scene: store %lu KB, recording %.1f s\n", (unsigned long)(part->size / 1024),
                storedFrames * FRAME_MS / 1000.0f);
}

Frame scenesUpdate(const PadState &pad, const Frame &live, uint32_t now) {
  if (pad.connected && !wasConnected) shownMode = (SceneMode)-1;  // fresh connection: resend the light bar
  wasConnected = pad.connected;

  // Controller: takeover stops any scene; Triangle / Circle / Share are commands
  if (pad.connected && pad.takeover) {
    lastActivity = lastTakeover = now;
    if (mode == M_IDLE || mode == M_PLAY || mode == M_SLEEP) stopScene();
    if (mode != M_RECORD) mode = M_LIVE;
  }
  bool tri = pad.connected && pad.triangle, cir = pad.connected && pad.circle,
       sh = pad.connected && pad.share;
  // Edges, not held buttons: a held Triangle must not undo the hold its own press set
  if ((pad.connected && pad.takeover) || (tri && !prevTri) || (cir && !prevCir) || (sh && !prevShare))
    holdRest = false;
  if (tri && !prevTri) {
    lastActivity = now;
    if (mode == M_IDLE) { stopScene(); holdRest = true; }
    else if (settings.idleMode != 0) startIdle(now, true);
  }
  if (cir && !prevCir) {
    lastActivity = now;
    if (mode == M_PLAY) stopScene();
    else startPlay(now, false);
  }
  if (sh && !prevShare) {
    lastActivity = now;
    if (mode == M_RECORD) finishRecording();
    else startRecord();
  }
  prevTri = tri;
  prevCir = cir;
  prevShare = sh;
  if (mode == M_RECORD && !pad.connected) finishRecording();

  bool unattended = now - lastActivity >= settings.autoIdleSecs * 1000UL;

  // Timers
  if (mode == M_IDLE && settings.idleMode == 0) mode = M_REST;
  if (mode == M_IDLE && idleUntil && (int32_t)(now - idleUntil) >= 0) { mode = M_REST; holdRest = true; }
  if (mode == M_LIVE && now - lastTakeover > 3000) mode = M_REST;
  if (settings.idleMode == 1 && mode == M_REST && unattended && !holdRest) startIdle(now, false);
  if (emptyPending && now - emptySince >= settings.emptyMins * 60000UL) {
    emptyPending = false;
    if (unattended && mode != M_RECORD && settings.emptyAction != 0) {
      stopScene();
      if (settings.emptyAction == 2) mode = M_SLEEP;
      else holdRest = true;
    }
  }

  Frame out = live;
  switch (mode) {
    case M_IDLE:
      out = idleFrame(now);
      break;
    case M_PLAY:
      if (!playFrame(now, out)) {
        mode = M_REST;
        if (playThenIdle) startIdle(now, true);
        out = mode == M_IDLE ? idleFrame(now) : live;
      }
      break;
    case M_SLEEP:
      out = {0, 0, true, settings.lidClosed};
      break;
    case M_RECORD:
      recordSample(live, now);
      break;
    default:
      break;
  }

  if (mode != shownMode) {
    Serial.printf("Scene: %s\n", sceneModeName());
    setLightBar(mode);
    shownMode = mode;
  }
  return out;
}

SceneMode sceneMode() { return mode; }

const char *sceneModeName() {
  switch (mode) {
    case M_LIVE: return "live";
    case M_IDLE: return "idle";
    case M_PLAY: return "play";
    case M_RECORD: return "record";
    case M_SLEEP: return "sleep";
    default: return "rest";
  }
}

bool sceneCommand(const String &cmd) {
  uint32_t now = millis();
  holdRest = false;
  if (cmd == "idle") return startIdle(now, true);
  else if (cmd == "play") return startPlay(now, false);
  else if (cmd == "record") return startRecord();
  else if (cmd == "stop") { stopScene(); holdRest = true; }
  else if (cmd == "sleep") { stopScene(); mode = M_SLEEP; }
  else if (cmd == "wake") { if (mode == M_SLEEP) mode = M_REST; }
  else return false;
  lastActivity = now;  // a page command counts as someone being there
  return true;
}

void scenePresence(bool on) {
  uint32_t now = millis();
  present = on;
  if (!on) {
    emptyPending = true;
    emptySince = now;
    return;
  }
  emptyPending = false;
  holdRest = false;
  if (mode == M_SLEEP) mode = M_REST;
  bool recentlyDriven = now - lastActivity < settings.autoIdleSecs * 1000UL;
  if (recentlyDriven || mode == M_RECORD || mode == M_PLAY || mode == M_IDLE) return;
  if (settings.arriveAction == 1) startIdle(now, true);
  else if (settings.arriveAction == 2 && !startPlay(now, true)) startIdle(now, true);
}

bool scenePresent() { return present; }
bool sceneHeld() { return holdRest; }

uint32_t recordingMs() { return storedFrames * FRAME_MS; }
