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
//  D-pad up/dn  lid trim (the kit's pot on A2)
//  No controller: eyes at their rest position, lids at the power-up opening.
//  Rest position, power-up lids, blink button and trim step: web page (WebUi.h).

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <PS4Controller.h>
#include <esp_mac.h>
#include <WiFi.h>
#include "secrets.h"   // WIFI_SSID / WIFI_PASS, git-ignored; see secrets.h.template
#include "EyeSettings.h"
#include "WebUi.h"
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

// Where the eyes rest with the stick centred (settings.parkY / parkX, set from the
// web page) is an offset from mechanical centre in the kit's 0..1023 units.
// Full stick travel still reaches both ends.
int restX() { return 512 + settings.parkX; }
int restY() { return 512 - settings.parkY; }

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

int xval = 512;
int yval = 512;
int switchval = LOW;
int trimval = 40;         // -40..40, same as the kit's pot after its map(); set from settings.bootTrim

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
  if (key == "bootTrim" || key == "") trimval = settings.bootTrim;
}

String eyeStatusJson() {
  char buf[160];
  snprintf(buf, sizeof buf, "{\"conn\":%s,\"ip\":\"%s\",\"heap\":%lu,\"build\":\"%s\",\"trim\":%d}",
           PS4.isConnected() ? "true" : "false", WiFi.localIP().toString().c_str(),
           (unsigned long)ESP.getFreeHeap(), BUILD_ID_STR, trimval);
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
  trimval = settings.bootTrim;
  xval = restX();
  yval = restY();

  wifiStart();
  webBegin();

  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
  delay(10);
}

void readController() {
  if (!PS4.isConnected()) {
    xval = restX();
    yval = restY();
    switchval = LOW;
    return;
  }
  xval = stickToAdc(stronger(PS4.LStickX(), PS4.RStickX()), INVERT_X, restX());
  yval = stickToAdc(stronger(PS4.LStickY(), PS4.RStickY()), INVERT_Y, restY());
  bool blink = settings.blinkBtn == 0 ? PS4.Cross()
             : settings.blinkBtn == 1 ? PS4.Square()
             : (PS4.Cross() || PS4.Square());
  switchval = blink ? HIGH : LOW;

  bool up = PS4.Up(), down = PS4.Down();
  if (up && !lastUp)     trimval = constrain(trimval + settings.trimStep, -40, 40);
  if (down && !lastDown) trimval = constrain(trimval - settings.trimStep, -40, 40);
  lastUp = up;
  lastDown = down;
}

void loop() {
  loopCount++;
  webHandle();
  if (Serial.available() && Serial.read() == 'w') {
    wifiWanted = !wifiWanted;
    wifiWanted ? wifiStart() : wifiStop();
  }
  if (millis() - lastStat >= 1000) {
    lastStat = millis();
    printStat();
  }

  readController();

  lexpulse = map(xval, 0, 1023, 220, 440);
  rexpulse = lexpulse;

  leypulse = map(yval, 0, 1023, 250, 500);
  reypulse = map(yval, 0, 1023, 400, 280);

  uplidpulse = map(yval, 0, 1023, 400, 280);
  uplidpulse -= (trimval - 40);
  uplidpulse = constrain(uplidpulse, 280, 400);
  altuplidpulse = 680 - uplidpulse;

  lolidpulse = map(yval, 0, 1023, 410, 280);
  lolidpulse += (trimval / 2);
  lolidpulse = constrain(lolidpulse, 280, 400);
  altlolidpulse = 680 - lolidpulse;

  pwm.setPWM(0, 0, lexpulse);
  pwm.setPWM(1, 0, leypulse);

  if (switchval == HIGH) {
    pwm.setPWM(2, 0, 400);
    pwm.setPWM(3, 0, 240);
    pwm.setPWM(4, 0, 240);
    pwm.setPWM(5, 0, 400);
  } else {
    pwm.setPWM(2, 0, uplidpulse);
    pwm.setPWM(3, 0, lolidpulse);
    pwm.setPWM(4, 0, altuplidpulse);
    pwm.setPWM(5, 0, altlolidpulse);
  }

  if (millis() - lastPrint > 200) {
    lastPrint = millis();
    Serial.printf("conn=%d x=%d y=%d blink=%d trim=%d\n",
                  PS4.isConnected(), xval, yval, switchval, trimval);
  }

  delay(5);
}
