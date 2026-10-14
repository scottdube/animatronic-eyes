//  Nilheim Mechatronics Basic EyeMech, driven by a PS4 (DS4) controller.
//  Board: ESP32-WROOM-32 DevKit. PCA9685 on I2C (SDA 21, SCL 22).
//  Libraries: Adafruit PWM Servo Driver, PS4Controller (pablomarquez76 fork).
//
//  Rebuilt 2026-09-24 from the stock Low_Tier_Code: the original controller
//  version was lost. The servo math below is the kit's, unchanged. Only the
//  inputs are new, converted to the 0..1023 range the kit's analogRead gave.
//
//  Either stick eyes (X and Y, lids follow Y as in the kit); per axis, the
//               stick pushed further wins
//  Cross        blink (the kit's button on D2)
//  D-pad up/dn  lid preset: closed < squint < normal < wide (replaces the kit's trim pot)
//  Triangle     alive idle on / off       Circle  play the recording / stop
//  Share        record / stop
//  Sticks, blink or D-pad take over from any scene (Scenes.h).
//  No controller: rest position, or alive idle after a while (settings).
//  Everything adjustable is on the web page (WebUi.h).

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <PS4Controller.h>
#include <esp_mac.h>
#include <esp_idf_version.h>
#include <esp_ota_ops.h>
#include <WiFi.h>
#include "secrets.h"   // WIFI_SSID / WIFI_PASS, git-ignored; see secrets.h.template
#include "EyeSettings.h"
#include "WebUi.h"
#include "Scenes.h"
#include "Rail.h"
#if __has_include("build_id.h")
#include "build_id.h"
#endif
#ifdef BUILD_ID
#define BUILD_ID_STR BUILD_ID
#else
#define BUILD_ID_STR "unknown"
#endif

// esp32 core 3.x frees the Bluetooth controller's memory at boot unless a BT
// library registers itself, and PS4Controller predates that and doesn't. Without
// this override PS4.begin() fails with "Bluetooth FAILED to start".
extern "C" bool btInUse() { return true; }

// The controller only connects to the Bluetooth MAC it has stored. Leave this
// empty to use the ESP32's own MAC (printed at boot); otherwise set it to the
// MAC the controller is paired to, e.g. "a0:5a:5c:12:34:56".
const char* PS4_HOST_MAC = "";

// Base MAC this board adopts at boot, or "" for the chip's own. The controller is bonded to
// the retired DevKit (base d4:8a:fc:9e:7a:cc; BT = base + 2, IDF's rule), and the UniFi
// reservation for 192.168.30.211 is on that Wi-Fi MAC, so the D1 Mini takes the whole
// identity: applied before any radio starts, Wi-Fi and BT both derive from it, and
// PS4.begin() needs no argument. A no-op on the DevKit itself. Two live boards on one MAC
// fight, so the DevKit stays unpowered once this runs on the D1 Mini.
const char* BOARD_BASE_MAC = "d4:8a:fc:9e:7a:cc";

static void adoptBaseMac() {
  uint8_t base[6];
  if (!strlen(BOARD_BASE_MAC)) return;
  if (sscanf(BOARD_BASE_MAC, "%hhx:%hhx:%hhx:%hhx:%hhx:%hhx",
             &base[0], &base[1], &base[2], &base[3], &base[4], &base[5]) != 6) {
    Serial.printf("BOARD_BASE_MAC unparsable: %s\n", BOARD_BASE_MAC);
    return;
  }
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 4, 1)
  esp_err_t e = esp_iface_mac_addr_set(base, ESP_MAC_BASE);
#else
  esp_err_t e = esp_base_mac_addr_set(base);
#endif
  Serial.printf("Base MAC %s: %s\n", BOARD_BASE_MAC, esp_err_to_name(e));
}

// Flip if an axis moves the wrong way on the real mechanism.
const bool INVERT_X = false;
const bool INVERT_Y = false;

// Rest position: restX()/restY() in EyeSettings.h. Full stick travel still
// reaches both ends.

// I2C to the PCA9685. The carrier routes SDA/SCL to IO27/IO25 (pads 24/26): IO21/IO22 are
// inner-row pins with no way out on a single-sided board. The retired DevKit used 21/22.
const int I2C_SDA = 27;
const int I2C_SCL = 25;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// The PCA9685 is set up once at boot. If its logic power blinks (a bumped jumper)
// it resets into sleep with every output off, and the ESP32 keeps writing positions
// it ignores: nothing moves, not even a buzz (seen 2026-09-24). Once a second the
// prescaler is read back; if it isn't ours, the chip is set up again.
// 60 Hz on the internal 25 MHz oscillator: 25e6 / (4096 * 60) - 1, rounded as Adafruit's
// setPWMFreq() does. The check compares against this, not against whatever the chip read
// back at boot: a dead module on the carrier (2026-09-28) read 254 every time, matched
// itself, and reported pca true while every output sat at 0 V.
const uint8_t PCA_PRESCALE_60HZ = 101;
uint8_t pcaPrescale = 0;
bool pcaOk = false;
uint32_t pcaResets = 0;
unsigned long lastPcaCheck = 0;

void pcaSetup() {
  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
  delay(10);
  pcaPrescale = pwm.readPrescale();
}

void pcaCheck() {
  uint8_t p = pwm.readPrescale();
  pcaPrescale = p;
  pcaOk = p == PCA_PRESCALE_60HZ;
  if (!pcaOk) {
    pcaResets++;
    Serial.printf("PCA9685: prescale read %u, expected %u - setting it up again (#%lu)\n",
                  p, PCA_PRESCALE_60HZ, (unsigned long)pcaResets);
    pcaSetup();
  }
}

// GET /pca: the chip's own registers, for when I2C answers but nothing moves (2026-09-28,
// carrier bring-up). The prescale alone can't see a stopped oscillator (MODE1 SLEEP/EXTCLK)
// or an ALL_LED full-off. -1 = the read failed.
// addr: 0x40 is the eyes' chip; any other address is a second module wired onto the same
// bus for testing (the reflowed dead module at 0x41, 2026-09-28).
int pcaReg(uint8_t reg, uint8_t addr = 0x40) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return -1;
  if (Wire.requestFrom(addr, (uint8_t)1) != 1) return -1;
  return Wire.read();
}

bool pcaWrite(uint8_t addr, uint8_t reg, uint8_t val) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.write(val);
  return Wire.endTransmission() == 0;
}

// POST /pcatest?out=high|low|run: hold channels 0-5 full-on (steady 3.3 V) or full-off,
// bypassing the PWM counter, so a meter can tell a dead output stage from a stopped
// counter. run = back to normal. Not saved; a restart is back to run.
int8_t pcaTest = 0;  // 0 run, 1 high, -1 low
void setPcaTest(int8_t t) {
  pcaTest = t;
  for (int ch = 0; ch <= 5; ch++) {
    if (t > 0) pwm.setPWM(ch, 4096, 0);
    else if (t < 0) pwm.setPWM(ch, 0, 4096);
  }
}

// The same test on a second module at another address, by raw register writes so the eyes'
// driver and its 0x40 watchdog are untouched. Sets the chip up first (a fresh module powers
// up asleep at prescale 30): sleep, prescale 101, wake with auto-increment, totem-pole.
// t: 1 full-on, -1 full-off, 2 = 1.5 ms pulses (369 counts at 60 Hz, a servo's centre).
// Returns false if the chip didn't ACK.
bool setPcaTestAt(uint8_t addr, int8_t t) {
  if (!pcaWrite(addr, 0x00, 0x10)) return false;  // MODE1: SLEEP (prescale is only writable asleep)
  pcaWrite(addr, 0xFE, PCA_PRESCALE_60HZ);
  pcaWrite(addr, 0x00, 0x20);                     // MODE1: awake, auto-increment
  delay(1);                                       // oscillator start-up, 500 us max
  pcaWrite(addr, 0x01, 0x04);                     // MODE2: totem-pole outputs
  for (uint8_t ch = 0; ch <= 5; ch++) {
    uint8_t b = 0x06 + 4 * ch;  // ON_L, ON_H, OFF_L, OFF_H
    uint16_t off = t == 2 ? 369 : 0;
    pcaWrite(addr, b, 0);
    pcaWrite(addr, b + 1, t == 1 ? 0x10 : 0);
    pcaWrite(addr, b + 2, off & 0xFF);
    pcaWrite(addr, b + 3, t == -1 ? 0x10 : off >> 8);
  }
  return true;
}

String pcaRegsJson(uint8_t addr) {
  String s = "{\"addr\":" + String(addr) + ",\"mode1\":" + String(pcaReg(0x00, addr)) +
             ",\"mode2\":" + String(pcaReg(0x01, addr)) +
             ",\"prescale\":" + String(pcaReg(0xFE, addr)) + ",\"allLed\":[";
  for (uint8_t r = 0xFA; r <= 0xFD; r++) s += String(pcaReg(r, addr)) + (r < 0xFD ? "," : "");
  s += "],\"ch\":[";
  for (uint8_t ch = 0; ch < 6; ch++) {  // ON_L, ON_H, OFF_L, OFF_H per channel
    s += "[";
    for (uint8_t i = 0; i < 4; i++) s += String(pcaReg(0x06 + 4 * ch + i, addr)) + (i < 3 ? "," : "");
    s += ch < 5 ? "]," : "]";
  }
  return s + "]}";
}

int xval = 512;
int yval = 512;
int switchval = LOW;
int lidIdx = 2;           // lid preset: 0 closed, 1 squint, 2 normal (power-up), 3 wide
void setLidPreset(int idx) { lidIdx = constrain(idx, 0, 3); }  // Scenes: service holds closed
const int DEADZONE = 16;  // stick movement past this is a takeover
Frame live;               // what the controller says this loop
PadState pad;

int lexpulse, rexpulse;
int leypulse, reypulse;
int uplidpulse, lolidpulse, altuplidpulse, altlolidpulse;

bool lastUp = false, lastDown = false;
unsigned long lastPrint = 0;

// Wi-Fi + Bluetooth coexistence check (step 1 of OTA/settings). Wi-Fi and the
// controller's Bluetooth share one radio on this ESP32. Once a second, print the
// controller's packet rate and the loop rate. Send 'w' on serial to switch Wi-Fi off
// and on, so both can be compared without a restart (a restart drops the controller).
const char* HOSTNAME = "eyemech";
volatile uint32_t pktCount = 0;
uint32_t loopCount = 0;
unsigned long lastStat = 0;
bool wifiWanted = true;

// Controller battery from its status byte, kept after a disconnect so a drop can be read
// against the level it last reported. DS4 scale: 0..10 on battery, up to 11 (full) charging.
volatile int8_t battLast = -1;
volatile bool battCharging = false;

void onPacket() {
  pktCount++;
  battLast = PS4.Battery();
  battCharging = PS4.Charging();
}

// WebUi hooks
void applyLiveSetting(const String &key) {
  // Lid opening shows immediately, so the slider can be judged by eye
  // Setting a lid preset shows it: stop any scene and switch to that preset
  static const char *const PRESETS[] = {"lidClosed", "lidSquint", "lidNormal", "lidWide"};
  for (int i = 0; i < 4; i++)
    if (key == PRESETS[i]) {
      sceneCommand("stop");
      lidIdx = i;
    }
  if (key == "lowLidCurve") sceneCommand("stop");  // hold still so the bottoms can be judged
  // A lid trim shows the end it trims: closed trims on the closed preset, open trims on wide
  // A lid trim shows the preset it trims (cLTop = closed, sLTop = squint, ...)
  if (key.length() == 5 && strchr("csnw", key[0]) && (key[1] == 'L' || key[1] == 'R')) {
    sceneCommand("stop");
    lidIdx = strchr("csnw", key[0]) - "csnw";
  }
  if (key == "") lidIdx = 2;
  // Setting the pupil center: hold the eyes there so it can be judged by eye
  if (key == "parkX" || key == "parkY") sceneCommand("stop");
  // Calibrating the center: stop a show, but keep a held look so an end stop can be checked
  if ((key == "xCenter" || key == "yCenter" || key == "upMax") && sceneMode() != M_REST) sceneCommand("stop");
}

String eyeStatusJson() {
  char buf[640];
  const esp_partition_t *run = esp_ota_get_running_partition();  // which OTA slot booted
  snprintf(buf, sizeof buf,
           "{\"conn\":%s,\"ip\":\"%s\",\"heap\":%lu,\"build\":\"%s\",\"slot\":\"%s\",\"lid\":%d,"
           "\"mode\":\"%s\",\"nextShow\":%d,\"showLeft\":%d,\"present\":%s,\"recMs\":%lu,\"x\":%d,\"y\":%d,\"pca\":%s,\"pcaPrescale\":%u,\"pcaResets\":%lu,"
           "\"rail\":%d,\"railMin\":%d,\"railMax\":%d,\"railDips\":%lu,\"reset\":\"%s\",\"batt\":%d,\"charging\":%s,\"test\":\"%s\"}",
           PS4.isConnected() ? "true" : "false", WiFi.localIP().toString().c_str(),
           (unsigned long)ESP.getFreeHeap(), BUILD_ID_STR, run ? run->label : "?", lidPct(lidIdx),
           sceneModeName(), sceneNextShowSecs(), sceneShowLeftSecs(), scenePresent() ? "true" : "false", (unsigned long)recordingMs(), xval, yval,
           pcaOk ? "true" : "false", pcaPrescale, (unsigned long)pcaResets,
           railNowMv(), railMinMv(), railMaxMv(), (unsigned long)railDips(), resetReasonName(),
           battLast, battCharging ? "true" : "false", sceneTestLabel().c_str());
  return buf;
}

void wifiStart() {
  WiFi.mode(WIFI_STA);
  WiFi.setHostname(HOSTNAME);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.println("WiFi: connecting");
}

void wifiStop() {
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  Serial.println("WiFi: off");
}

void printStat() {
  uint32_t pkts = pktCount;
  pktCount = 0;
  if (WiFi.status() == WL_CONNECTED)
    Serial.printf("stat pkts/s=%lu loop/s=%lu wifi=%s rssi=%d heap=%lu\n",
                  (unsigned long)pkts, (unsigned long)loopCount,
                  WiFi.localIP().toString().c_str(), WiFi.RSSI(),
                  (unsigned long)ESP.getFreeHeap());
  else
    Serial.printf("stat pkts/s=%lu loop/s=%lu wifi=%s heap=%lu\n",
                  (unsigned long)pkts, (unsigned long)loopCount,
                  wifiWanted ? "down" : "off", (unsigned long)ESP.getFreeHeap());
  loopCount = 0;
}

// Stick -128..127 to 0..1023, with the stick's center landing on `center`, so
// each half of the travel is stretched to keep reaching its end.
int stickToAdc(int v, bool invert, int center) {
  if (invert) v = -v;
  return v < 0 ? map(v, -128, 0, 0, center) : map(v, 0, 127, center, 1023);
}

// Per axis, the stick pushed further from center wins, so either stick drives.
int stronger(int a, int b) {
  return abs(a) >= abs(b) ? a : b;
}

void onConnect() {
  Serial.println("PS4 connected");
  PS4.setLed(0, 0, 255);
  PS4.sendToController();
}

void onDisconnect() {
  Serial.printf("PS4 disconnected (battery %d%s at the last packet)\n", battLast, battCharging ? ", charging" : "");
}

void setup() {
  Serial.begin(115200);
  Serial.println("EyeMech PS4");
  Serial.printf("Last restart: %s\n", resetReasonName());
  adoptBaseMac();  // before railBegin/PS4/WiFi: nothing may have read the MAC yet
  railBegin();

  uint8_t m[6];
  esp_read_mac(m, ESP_MAC_BT);
  Serial.printf("ESP32 Bluetooth MAC: %02x:%02x:%02x:%02x:%02x:%02x\n",
                m[0], m[1], m[2], m[3], m[4], m[5]);
  esp_read_mac(m, ESP_MAC_WIFI_STA);
  Serial.printf("ESP32 Wi-Fi MAC: %02x:%02x:%02x:%02x:%02x:%02x\n",
                m[0], m[1], m[2], m[3], m[4], m[5]);
  if (strlen(PS4_HOST_MAC)) Serial.printf("Using PS4_HOST_MAC: %s\n", PS4_HOST_MAC);

  bool ok = strlen(PS4_HOST_MAC) ? PS4.begin(PS4_HOST_MAC) : PS4.begin();
  Serial.println(ok ? "Bluetooth up" : "Bluetooth FAILED to start");
  PS4.attachOnConnect(onConnect);
  PS4.attachOnDisconnect(onDisconnect);
  PS4.attach(onPacket);

  loadSettings();
  lidIdx = 2;
  xval = restX();
  yval = restY();
  scenesBegin();
  scenesBoot();

  wifiStart();
  webBegin();

  Wire.begin(I2C_SDA, I2C_SCL);  // once: pcaCheck() re-runs pcaSetup() on the live bus
  pcaSetup();
  pcaOk = pcaPrescale == PCA_PRESCALE_60HZ;
  Serial.printf("PCA9685: prescale %u (%s)\n", pcaPrescale, pcaOk ? "answering" : "NOT answering");
}

int lidPct(int idx) {
  switch (idx) {
    case 0: return settings.lidClosed;
    case 1: return settings.lidSquint;
    case 3: return settings.lidWide;
    default: return settings.lidNormal;
  }
}

// Fills `live` and `pad`. No controller = rest, lids at the preset where they were left.
void readController() {
  pad = PadState{};
  live = Frame{0, 0, false, lidPct(lidIdx)};
  if (!PS4.isConnected()) return;
  pad.connected = true;
  live.sx = stronger(PS4.LStickX(), PS4.RStickX());
  live.sy = stronger(PS4.LStickY(), PS4.RStickY());
  live.blink = settings.blinkBtn == 0 ? PS4.Cross()
             : settings.blinkBtn == 1 ? PS4.Square()
             : (PS4.Cross() || PS4.Square());

  bool up = PS4.Up(), down = PS4.Down();
  if (up && !lastUp)     lidIdx = min(lidIdx + 1, 3);
  if (down && !lastDown) lidIdx = max(lidIdx - 1, 0);
  lastUp = up;
  lastDown = down;
  live.lid = lidPct(lidIdx);

  bool moved = abs(PS4.LStickX()) > DEADZONE || abs(PS4.LStickY()) > DEADZONE ||
               abs(PS4.RStickX()) > DEADZONE || abs(PS4.RStickY()) > DEADZONE;
  pad.takeover = moved || live.blink || up || down || PS4.Left() || PS4.Right();
  pad.triangle = PS4.Triangle();
  pad.circle = PS4.Circle();
  pad.share = PS4.Share();
}

// The kit's lid pulse with the two lid settings applied. `kit` is the kit's
// map() of Y, `center` the same map() at mechanical center (512): lidFollow
// scales how far the lid moves away from that with the eyes.
int followLid(int kit, int center) {
  return center + (kit - center) * settings.lidFollow / 100;
}

// Trim for lid l at `pct` % open: each preset's trim sits at that preset's own %, and
// in between (idle's moves, a blink on the way down) it blends linearly.
float trimAt(int l, int pct) {
  int idx[4] = {0, 1, 2, 3};
  for (int a = 1; a < 4; a++)  // presets sorted by their % (the sliders can reorder them)
    for (int b = a; b > 0 && lidPct(idx[b]) < lidPct(idx[b - 1]); b--) std::swap(idx[b], idx[b - 1]);
  if (pct <= lidPct(idx[0])) return lidTrim(idx[0], l);
  for (int k = 1; k < 4; k++) {
    int p0 = lidPct(idx[k - 1]), p1 = lidPct(idx[k]);
    if (pct <= p1) {
      if (p1 == p0) return lidTrim(idx[k], l);
      return lidTrim(idx[k - 1], l) + (lidTrim(idx[k], l) - lidTrim(idx[k - 1], l)) * float(pct - p0) / (p1 - p0);
    }
  }
  return lidTrim(idx[3], l);
}

// One lid servo: the untrimmed pulse plus the trim in the direction that opens it
// (dir -1: pulse falls as the lid opens), clamped to the SG90's safe ~0.6-2.4 ms.
int lidPulse(float base, int dir, float trim) {
  return constrain((int)lroundf(base + dir * trim), 150, 600);
}

void loop() {
  loopCount++;
  webHandle();
  if (Serial.available() && Serial.read() == 'w') {
    wifiWanted = !wifiWanted;
    wifiWanted ? wifiStart() : wifiStop();
  }
  if (millis() - lastPcaCheck >= 1000) {
    lastPcaCheck = millis();
    pcaCheck();
  }
  if (millis() - lastStat >= 1000) {
    lastStat = millis();
    printStat();
  }

  readController();
  Frame f = scenesUpdate(pad, live, millis());
  xval = stickToAdc(f.sx, INVERT_X, restX());
  yval = stickToAdc(f.sy, INVERT_Y, restY());
  switchval = f.blink ? HIGH : LOW;
  int lid = f.blink ? settings.lidClosed : f.lid;  // % open; a blink goes to the closed preset
  // Per eye, his own left/right: a wink shuts one of them
  int lidL = f.wink == 1 ? settings.lidClosed : lid, lidR = f.wink == 2 ? settings.lidClosed : lid;

  lexpulse = constrain(map(xval, 0, 1023, 220, 440) + settings.xCenter, 150, 600);  // + xCenter: calibration
  rexpulse = lexpulse;

  // The kit's map(yval, 0..1023, 250..500), with the upper half ending at upMax
  int ey = yval <= 512 ? map(yval, 0, 512, 250, 375) : map(yval, 512, 1023, 375, settings.upMax);
  leypulse = constrain(ey + settings.yCenter, 150, 600);  // + yCenter: calibration
  reypulse = map(yval, 0, 1023, 400, 280);

  // Fully open: the kit's lids at trim 40, following the eyes, pushed out to the
  // open limits (lidMin below the kit's 280, lowLidMax above its 400).
  int upOpen = followLid(map(yval, 0, 1023, 400, 280), 340) - (280 - settings.lidMin);
  upOpen = constrain(upOpen, settings.lidMin, 400);
  int loOpen = followLid(map(yval, 0, 1023, 410, 280), 345) + 20 + (settings.lowLidMax - 400);
  loOpen = constrain(loOpen, 280, settings.lowLidMax);
  // Each servo goes between its own closed pulse (the kit's blink, which the horns
  // were seated to) and its open pulse. The kit's blink is not an exact mirror, so
  // servos 4 and 5 get their own closed values rather than 680 - x.
  // Bottom lids follow the top on a curve (lowLidCurve): 50 = sqrt, mostly open until
  // nearly shut like the kit's trim; 100 = same % as the top. 0% and 100% always
  // stay closed and open, so blink and wide are unchanged.
  // Servos 2+3 are HIS left eye, 4+5 his right (the eye on your left as you face him).
  float topL = lidL / 100.0f, botL = powf(topL, settings.lowLidCurve / 100.0f);
  float topR = lidR / 100.0f, botR = powf(topR, settings.lowLidCurve / 100.0f);
  uplidpulse = lidPulse(400 + (upOpen - 400) * topL, -1, trimAt(0, lidL));            // his left, top
  lolidpulse = lidPulse(240 + (loOpen - 240) * botL, +1, trimAt(1, lidL));            // his left, bottom
  altuplidpulse = lidPulse(240 + ((680 - upOpen) - 240) * topR, +1, trimAt(2, lidR)); // his right, top
  altlolidpulse = lidPulse(400 + ((680 - loOpen) - 400) * botR, -1, trimAt(3, lidR)); // his right, bottom

  if (pcaTest) {
    // /pcatest holds the outputs; leave them alone
  } else {
    // Quiet sleep (limp) and the noise test's idle servos get no pulses at all (the PCA9685's
    // full-off bit), so they can't hum
    int pulse[6] = {lexpulse, leypulse, uplidpulse, lolidpulse, altuplidpulse, altlolidpulse};
    uint8_t on = f.limp ? 0 : f.power;
    for (int ch = 0; ch <= 5; ch++) {
      if (on & (1 << ch)) pwm.setPWM(ch, 0, pulse[ch]);
      else pwm.setPWM(ch, 0, 4096);
    }
  }

  if (millis() - lastPrint > 200) {
    lastPrint = millis();
    Serial.printf("conn=%d mode=%s x=%d y=%d blink=%d lid=%d\n",
                  PS4.isConnected(), sceneModeName(), xval, yval, switchval, lid);
  }

  delay(5);
}
