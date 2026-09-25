#include "Scenes.h"
#include "EyeSettings.h"
#include <PS4Controller.h>
#include <esp_partition.h>
#include <math.h>

// ---- state ----------------------------------------------------------------
// Everyday use (Scott, 2026-09-25): walk in, 30 s later the eyes wake and do a short
// show, then sleep; the servos are loud, so they must NOT run the whole time he is in
// the lab. Another show comes on a return after the lab was empty a while, and every
// showEvery minutes while he is there. Extended play is on demand (HA voice or page).
static SceneMode mode = M_REST, shownMode = (SceneMode)-1, prevMode = M_REST;
static uint32_t lastTakeover = 0;
static bool prevTri = false, prevCir = false, prevShare = false;

static uint32_t idleUntil = 0;  // end of the current show
static bool playThenIdle = false;

static bool present = false, everPresent = false;
static uint32_t emptySince = 0;
static bool showPending = false;  // an arrival show waiting out arriveDelay
static uint32_t showAt = 0;
static uint32_t nextPeriodic = 0;  // 0 = none (nobody present, or showEvery 0)
static bool sleepAfterHands = false;  // the controller was let go: sleep after handsOffSecs
static uint32_t sleepSince = 0;
static bool wasConnected = false;

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
// Set pieces inside a show (Scott, 2026-09-25). Times in ms.
// Wake: a show that starts from sleep opens wide and looks far to his left first.
static const uint32_t WAKE_MS = 2500;
static uint32_t wakeUntil = 0;
// Slow squint: wide, close slowly to squint, then a slow look side to side, then carry on.
static const uint32_t SQ_OPEN = 600, SQ_CLOSE = 3000, SQ_PAN = 6000, SQ_BACK = 600;
static uint32_t squintAt = 0;   // start of the next (or running) slow squint
// Winks: now and then one eye closes, either eye.
static const uint32_t WINK_MS = 400;
static uint32_t nextWink = 0, winkEnd = 0;
static int winkEye = 0;

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

static uint32_t randMs(uint32_t lo, uint32_t hi) { return lo + (uint32_t)(frand() * (hi - lo)); }

static void idleReset(uint32_t now, bool fromSleep) {
  tx = ty = 0;
  wakeUntil = fromSleep ? now + WAKE_MS : now;
  squintAt = wakeUntil + randMs(20000, 40000);
  nextWink = wakeUntil + randMs(15000, 45000);
  winkEnd = 0;
  nextGlance = now + 300;
  nextDrift = now + 400;
  nextBlink = now + nextBlinkDelay();
  blinkEnd = secondBlink = 0;
  idleLidUntil = 0;
  lastIdleUpdate = now;
}

// Far to his left: + x is his left (measured 2026-09-25), kept a little off the end stop
static float farLeft() { return 1023 - 40 - restX(); }

// The set pieces; true = this frame is theirs and ordinary idle waits
static bool setPiece(uint32_t now, Frame &f) {
  float dt = (float)(now - lastIdleUpdate);
  if (now < wakeUntil) {  // wake: wide, eyes swing far left and hold
    tx = farLeft();
    ty = 0;
    gx += (tx - gx) * (1.0f - expf(-dt / 150.0f));
    gy += (ty - gy) * (1.0f - expf(-dt / 150.0f));
    f.lid = settings.lidWide;
    return true;
  }
  if (now < squintAt) return false;
  uint32_t t = now - squintAt;
  float R = settings.glanceRange / 100.0f * IDLE_X_MAX;
  if (t < SQ_OPEN) {  // wide, eyes back to center
    gx += (0 - gx) * (1.0f - expf(-dt / 150.0f));
    gy += (0 - gy) * (1.0f - expf(-dt / 150.0f));
    f.lid = settings.lidWide;
  } else if ((t -= SQ_OPEN) < SQ_CLOSE) {  // slowly down to squint
    f.lid = settings.lidWide + (settings.lidSquint - settings.lidWide) * (float)t / SQ_CLOSE;
  } else if ((t -= SQ_CLOSE) < SQ_PAN) {  // one slow sweep: his left, across to his right, back
    gx = R * sinf(2 * (float)M_PI * t / SQ_PAN);
    f.lid = settings.lidSquint;
  } else if ((t -= SQ_PAN) < SQ_BACK) {
    gx = 0;
    f.lid = settings.lidNormal;
  } else {  // done: the next one in about a minute
    tx = ty = gx = 0;
    squintAt = now + randMs(45000, 75000);
    nextGlance = nextBlink = now + 300;
    return false;
  }
  return true;
}

static Frame idleFrame(uint32_t now) {
  Frame f;
  if (setPiece(now, f)) {
    lastIdleUpdate = now;
    blinkEnd = secondBlink = winkEnd = 0;
    f.sx = adcToStick(gx, restX());
    f.sy = adcToStick(gy, restY());
    f.blink = false;
    return f;
  }
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
  if (now >= nextWink && now >= blinkEnd) {  // a wink, either eye, a few per show
    winkEye = frand() < 0.5f ? 1 : 2;
    winkEnd = now + WINK_MS;
    nextWink = now + randMs(25000, 60000);
  }
  f.sx = adcToStick(gx, restX());
  f.sy = adcToStick(gy, restY());
  f.blink = now < blinkEnd;
  f.wink = now < winkEnd ? winkEye : 0;
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

// Where the eyes go when a show, a playback or the controller is done: asleep, unless
// shows are off altogether (then they rest open as before).
static void endScene() {
  stopScene();
  if (settings.idleMode != 0) mode = M_SLEEP;
}

static bool startShow(uint32_t now, uint32_t secs) {
  if (mode == M_RECORD || settings.idleMode == 0) return false;
  idleReset(now, mode == M_SLEEP);
  idleUntil = now + secs * 1000UL;
  mode = M_IDLE;
  showPending = false;
  sleepAfterHands = false;
  return true;
}

static bool startPlay(uint32_t now, bool thenIdle) {
  if (!storedFrames || mode == M_RECORD) return false;
  playThenIdle = thenIdle;
  playStart = now;
  showPending = false;
  sleepAfterHands = false;
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
    wbuf[wlen++] = (f.blink ? 1 : 0) | (f.wink & 3) << 1;  // bits 1-2: wink (old recordings: 0)
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
  f.wink = p[2] >> 1 & 3;
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

// An arrival (or power-up) show: what arriveAction says
static void arrivalShow(uint32_t now) {
  if (settings.arriveAction == 1) startShow(now, settings.showSecs);
  else if (settings.arriveAction == 2 && !startPlay(now, true)) startShow(now, settings.showSecs);
}

Frame scenesUpdate(const PadState &pad, const Frame &live, uint32_t now) {
  if (pad.connected && !wasConnected) shownMode = (SceneMode)-1;  // fresh connection: resend the light bar
  wasConnected = pad.connected;

  // Controller: takeover stops any scene; Triangle / Circle / Share are commands
  if (pad.connected && pad.takeover) {
    lastTakeover = now;
    showPending = false;  // driving during the arrival wait: no show on top of it
    if (mode == M_IDLE || mode == M_PLAY || mode == M_SLEEP) stopScene();
    if (mode != M_RECORD) mode = M_LIVE;
  }
  bool tri = pad.connected && pad.triangle, cir = pad.connected && pad.circle,
       sh = pad.connected && pad.share;
  if (tri && !prevTri) {
    if (mode == M_IDLE) endScene();
    else startShow(now, settings.showSecs);
  }
  if (cir && !prevCir) {
    if (mode == M_PLAY) endScene();
    else startPlay(now, false);
  }
  if (sh && !prevShare) {
    if (mode == M_RECORD) finishRecording();
    else startRecord();
  }
  prevTri = tri;
  prevCir = cir;
  prevShare = sh;
  if (mode == M_RECORD && !pad.connected) finishRecording();

  // Timers
  if (mode == M_IDLE && (settings.idleMode == 0 || (int32_t)(now - idleUntil) >= 0)) endScene();
  if (mode == M_LIVE && now - lastTakeover > 3000) {
    mode = M_REST;
    sleepAfterHands = settings.idleMode != 0;
  }
  if (sleepAfterHands && mode == M_REST && now - lastTakeover >= settings.handsOffSecs * 1000UL) {
    sleepAfterHands = false;
    mode = M_SLEEP;
  }
  bool waiting = mode == M_REST || mode == M_SLEEP;
  if (showPending && (int32_t)(now - showAt) >= 0) {
    showPending = false;
    if (waiting) arrivalShow(now);
  }
  if (nextPeriodic && (int32_t)(now - nextPeriodic) >= 0) {
    nextPeriodic = (present && settings.showEvery) ? now + settings.showEvery * 60000UL : 0;
    if (settings.idleMode == 1 && present && settings.showEvery && waiting && !showPending)
      startShow(now, settings.showSecs);
  }

  if (mode != prevMode && mode == M_SLEEP) sleepSince = now;
  prevMode = mode;

  Frame out = live;
  switch (mode) {
    case M_IDLE:
      out = idleFrame(now);
      break;
    case M_PLAY:
      if (!playFrame(now, out)) {
        if (playThenIdle) startShow(now, settings.showSecs);
        else endScene();
        out = mode == M_IDLE ? idleFrame(now) : live;
      }
      break;
    case M_SLEEP:
      out = {0, 0, true, settings.lidClosed};
      // Quiet sleep: once the lids have had time to close, stop the pulses so the
      // cheap servos can't hum or buzz holding position.
      out.limp = settings.sleepQuiet && now - sleepSince > 1000;
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
  if (cmd == "idle" || cmd == "show") return startShow(now, settings.showSecs);
  else if (cmd == "extended") return startShow(now, settings.extendMins * 60UL);
  else if (cmd == "play") return startPlay(now, false);
  else if (cmd == "record") return startRecord();
  else if (cmd == "stop") stopScene();  // rest, eyes open, until something else happens
  else if (cmd == "sleep") { stopScene(); mode = M_SLEEP; }
  else if (cmd == "wake") { if (mode == M_SLEEP) mode = M_REST; }
  else return false;
  showPending = false;
  sleepAfterHands = false;
  return true;
}

void scenesBoot() {
  // Power-up counts as an arrival, so the cycle works before the radar reports anything
  if (settings.idleMode == 1) {
    showPending = true;
    showAt = millis() + settings.arriveDelay * 1000UL;
  }
}

void scenePresence(bool on) {
  uint32_t now = millis();
  if (on == present) return;  // Home Assistant may repeat itself
  present = on;
  if (!on) {
    emptySince = now;
    showPending = false;  // left during the wait: no show to an empty room
    nextPeriodic = 0;
    return;
  }
  if (mode == M_SLEEP && settings.idleMode == 0) mode = M_REST;
  nextPeriodic = settings.showEvery ? now + settings.showEvery * 60000UL : 0;
  // A new arrival only after the lab was empty emptyMins: a quick step out doesn't count
  bool arrival = !everPresent || now - emptySince >= settings.emptyMins * 60000UL;
  everPresent = true;
  if (!arrival || settings.idleMode != 1) return;
  if (mode == M_RECORD || mode == M_PLAY || mode == M_IDLE || mode == M_LIVE) return;
  showPending = true;
  showAt = now + settings.arriveDelay * 1000UL;
}

bool scenePresent() { return present; }

// Seconds to the next show the eyes will start on their own, -1 = none scheduled
int sceneNextShowSecs() {
  uint32_t now = millis();
  int32_t best = -1;
  if (showPending) best = max<int32_t>(0, (int32_t)(showAt - now));
  if (nextPeriodic && settings.idleMode == 1) {
    int32_t d = max<int32_t>(0, (int32_t)(nextPeriodic - now));
    if (best < 0 || d < best) best = d;
  }
  return best < 0 ? -1 : (int)(best / 1000);
}

// Seconds left in the running show, -1 = no show running
int sceneShowLeftSecs() {
  if (mode != M_IDLE) return -1;
  return max<int32_t>(0, (int32_t)(idleUntil - millis())) / 1000;
}

uint32_t recordingMs() { return storedFrames * FRAME_MS; }
