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
#include <esp_ota_ops.h>
#include <WiFi.h>
#include "secrets.h"   // WIFI_SSID / WIFI_PASS, git-ignored; see secrets.h.template
#include "EyeSettings.h"
#include "WebUi.h"
#include "Scenes.h"
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

// Flip if an axis moves the wrong way on the real mechanism.
const bool INVERT_X = false;
const bool INVERT_Y = false;

// Rest position: restX()/restY() in EyeSettings.h. Full stick travel still
// reaches both ends.

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// The PCA9685 is set up once at boot. If its logic power blinks (a bumped jumper)
// it resets into sleep with every output off, and the ESP32 keeps writing positions
// it ignores: nothing moves, not even a buzz (seen 2026-09-24). Once a second the
// prescaler is read back; if it isn't ours, the chip is set up again.
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
  pcaOk = p == pcaPrescale && p != 0 && p != 0xFF;
  if (!pcaOk) {
    pcaResets++;
    Serial.printf("PCA9685: prescale read %u, expected %u - setting it up again (#%lu)\n",
                  p, pcaPrescale, (unsigned long)pcaResets);
    uint8_t want = pcaPrescale;
    pcaSetup();
    if (want && want != 0xFF) pcaPrescale = want;
  }
}

int xval = 512;
int yval = 512;
int switchval = LOW;
int lidIdx = 2;           // lid preset: 0 closed, 1 squint, 2 normal (power-up), 3 wide
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

void onPacket() { pktCount++; }

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
  if (key == "") lidIdx = 2;
  // Setting the pupil centre: hold the eyes there so it can be judged by eye
  if (key == "parkX" || key == "parkY") sceneCommand("stop");
}

String eyeStatusJson() {
  char buf[320];
  const esp_partition_t *run = esp_ota_get_running_partition();  // which OTA slot booted
  snprintf(buf, sizeof buf,
           "{\"conn\":%s,\"ip\":\"%s\",\"heap\":%lu,\"build\":\"%s\",\"slot\":\"%s\",\"lid\":%d,"
           "\"mode\":\"%s\",\"present\":%s,\"recMs\":%lu,\"x\":%d,\"y\":%d,\"pca\":%s,\"pcaPrescale\":%u,\"pcaResets\":%lu}",
           PS4.isConnected() ? "true" : "false", WiFi.localIP().toString().c_str(),
           (unsigned long)ESP.getFreeHeap(), BUILD_ID_STR, run ? run->label : "?", lidPct(lidIdx),
           sceneModeName(), scenePresent() ? "true" : "false", (unsigned long)recordingMs(), xval, yval,
           pcaOk ? "true" : "false", pcaPrescale, (unsigned long)pcaResets);
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

// Stick -128..127 to 0..1023, with the stick's centre landing on `centre`, so
// each half of the travel is stretched to keep reaching its end.
int stickToAdc(int v, bool invert, int centre) {
  if (invert) v = -v;
  return v < 0 ? map(v, -128, 0, 0, centre) : map(v, 0, 127, centre, 1023);
}

// Per axis, the stick pushed further from centre wins, so either stick drives.
int stronger(int a, int b) {
  return abs(a) >= abs(b) ? a : b;
}

void onConnect() {
  Serial.println("PS4 connected");
  PS4.setLed(0, 0, 255);
  PS4.sendToController();
}

void onDisconnect() {
  Serial.println("PS4 disconnected");
}

void setup() {
  Serial.begin(115200);
  Serial.println("EyeMech PS4");

  uint8_t m[6];
  esp_read_mac(m, ESP_MAC_BT);
  Serial.printf("ESP32 Bluetooth MAC: %02x:%02x:%02x:%02x:%02x:%02x\n",
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

  wifiStart();
  webBegin();

  pcaSetup();
  pcaOk = pcaPrescale != 0 && pcaPrescale != 0xFF;
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
// map() of Y, `centre` the same map() at mechanical centre (512): lidFollow
// scales how far the lid moves away from that with the eyes.
int followLid(int kit, int centre) {
  return centre + (kit - centre) * settings.lidFollow / 100;
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

  lexpulse = map(xval, 0, 1023, 220, 440);
  rexpulse = lexpulse;

  leypulse = map(yval, 0, 1023, 250, 500);
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
  // Bottom lids close by sqrt: like real ones they stay mostly open until a lid nearly
  // shuts, which matches the kit's trim moving them half as far (normal 75% = trim 5).
  float top = lid / 100.0f, bot = sqrtf(top);
  uplidpulse = lroundf(400 + (upOpen - 400) * top);
  altuplidpulse = lroundf(240 + ((680 - upOpen) - 240) * top);
  lolidpulse = lroundf(240 + (loOpen - 240) * bot);
  altlolidpulse = lroundf(400 + ((680 - loOpen) - 400) * bot);

  pwm.setPWM(0, 0, lexpulse);
  pwm.setPWM(1, 0, leypulse);

  pwm.setPWM(2, 0, uplidpulse);
  pwm.setPWM(3, 0, lolidpulse);
  pwm.setPWM(4, 0, altuplidpulse);
  pwm.setPWM(5, 0, altlolidpulse);

  if (millis() - lastPrint > 200) {
    lastPrint = millis();
    Serial.printf("conn=%d mode=%s x=%d y=%d blink=%d lid=%d\n",
                  PS4.isConnected(), sceneModeName(), xval, yval, switchval, lid);
  }

  delay(5);
}
