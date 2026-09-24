//  Nilheim Mechatronics Basic EyeMech, driven by a PS4 (DS4) controller.
//  Board: ESP32-WROOM-32 DevKit. PCA9685 on I2C (SDA 21, SCL 22).
//  Libraries: Adafruit PWM Servo Driver, PS4Controller (pablomarquez76 fork).
//
//  Rebuilt 2026-09-24 from the stock Low_Tier_Code: the original controller
//  version was lost. The servo math below is the kit's, unchanged. Only the
//  inputs are new, converted to the 0..1023 range the kit's analogRead gave.
//
//  Left stick   eyes (X and Y, lids follow Y as in the kit)
//  Cross        blink (the kit's button on D2)
//  D-pad up/dn  lid trim (the kit's pot on A2)
//  No controller: eyes centred, lids open.

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <PS4Controller.h>

// The controller only connects to the Bluetooth MAC it has stored. Leave this
// empty to use the ESP32's own MAC (printed at boot); otherwise set it to the
// MAC the controller is paired to, e.g. "a0:5a:5c:12:34:56".
const char* PS4_HOST_MAC = "";

// Flip if an axis moves the wrong way on the real mechanism.
const bool INVERT_X = false;
const bool INVERT_Y = false;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

int xval = 512;
int yval = 512;
int switchval = LOW;
int trimval = 0;          // -40..40, same as the kit's pot after its map()

int lexpulse, rexpulse;
int leypulse, reypulse;
int uplidpulse, lolidpulse, altuplidpulse, altlolidpulse;

bool lastUp = false, lastDown = false;
unsigned long lastPrint = 0;

int stickToAdc(int8_t v, bool invert) {
  int a = map(v, -128, 127, 0, 1023);
  return invert ? 1023 - a : a;
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

  bool ok = strlen(PS4_HOST_MAC) ? PS4.begin(PS4_HOST_MAC) : PS4.begin();
  Serial.println(ok ? "Bluetooth up" : "Bluetooth FAILED to start");
  PS4.attachOnConnect(onConnect);
  PS4.attachOnDisconnect(onDisconnect);

  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
  delay(10);
}

void readController() {
  if (!PS4.isConnected()) {
    xval = 512;
    yval = 512;
    switchval = LOW;
    return;
  }
  xval = stickToAdc(PS4.LStickX(), INVERT_X);
  yval = stickToAdc(PS4.LStickY(), INVERT_Y);
  switchval = PS4.Cross() ? HIGH : LOW;

  bool up = PS4.Up(), down = PS4.Down();
  if (up && !lastUp)     trimval = constrain(trimval + 5, -40, 40);
  if (down && !lastDown) trimval = constrain(trimval - 5, -40, 40);
  lastUp = up;
  lastDown = down;
}

void loop() {
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
