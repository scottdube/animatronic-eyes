//  Nilheim Mechatronics Simplified Eye Mechanism Code
//  Make sure you have the Adafruit servo driver library installed >>>>> https://github.com/adafruit/Adafruit-PWM-Servo-Driver-Library
//  X-axis joystick pin: A1
//  Y-axis joystick pin: A0
//  Trim potentiometer pin: A2
//  Button pin: 2

#include <PS4Controller.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

//Start adafruit servo driver
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

int xval;
int yval;
int lexpulse;
int rexpulse;
int leypulse;
int reypulse;
int uplidpulse;
int lolidpulse;
int altuplidpulse;
int altlolidpulse;
int trimval;
int switchval = 0;

// Controller Joystick Values
int leftX;
int leftY;
int Blink;
int down_button;
int up_button;
int button_pos=50; //Initial lid position

// Servo Position
int servoPos = 135 ; // Up-down
int servoPos1 = 74; // left-right look

// Callback Function
void notify() {
 
  // Get Joystick value
  leftX = (PS4.LStickX());
  leftY = (PS4.LStickY());
  Blink = (PS4.Square());
  down_button = (PS4.Down());
  up_button = (PS4.Up());

  {
    // See if joystick was moved left or right, and in what direction. If moved, move servo in that direction
    if (leftX < -10 && servoPos1 >30) {
      servoPos1--;
      delay(10);
    }
    if (leftX > 10 && servoPos1 <120) {
      servoPos1++;
      delay(10);
    }
  // See if joystick was moved up or down, and in what direction. If moved, move servo in that direction
    
      if (leftY < -10 && servoPos >85) {
      servoPos--;
      delay(10);
    }
    if (leftY > 10 && servoPos <175) {
      servoPos++;
      delay(10);
    }
  }
}
  
// On Connection function
void onConnect() {
}

void setup() 
{

   // Define Callback Function

  PS4.attach(notify);

  // Define On Connection Function
  PS4.attachOnConnect(onConnect);

  Serial.begin(115200);
   PS4.begin();
    Serial.println("Ready.");

  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
  delay(10);
}

void loop() {

  xval = (leftX);
    lexpulse = map(xval, -127,127, 180, 440);
    rexpulse = lexpulse;
    
  yval = (leftY);
    leypulse = map(yval, -127,127, 250, 500);
    reypulse = map(yval, -127,127, 400, 280);

  trimval = button_pos;
     uplidpulse = map(yval, -127, 127, 400, 250);
        uplidpulse -= (trimval-40);
          uplidpulse = constrain(uplidpulse, 250, 400);
     altuplidpulse = 680-uplidpulse;

     lolidpulse = map(yval, -127, 127, 410, 280);
       lolidpulse += (trimval/2);
         lolidpulse = constrain(lolidpulse, 280, 400);      
     altlolidpulse = 680-lolidpulse;
      pwm.setPWM(0, 0, lexpulse);
      pwm.setPWM(1, 0, leypulse);

// eye blink code starts here
    switchval = (Blink);
      if (switchval == HIGH) {
      pwm.setPWM(2, 0, 400);
      pwm.setPWM(3, 0, 240);
      pwm.setPWM(4, 0, 240);
      pwm.setPWM(5, 0, 400);
      }
      else if (switchval == LOW) {
      pwm.setPWM(2, 0, uplidpulse);
      pwm.setPWM(3, 0, lolidpulse);
      pwm.setPWM(4, 0, altuplidpulse);
      pwm.setPWM(5, 0, altlolidpulse);
      }
      if (PS4.Up() && button_pos < 50) {
          button_pos+=25;
      }
      if (PS4.Down() && button_pos > -50){
         button_pos-=25; 
      }
      //Debug code

         // Serial.println("Connected.");
         //Serial.printf("Battery Level : %d\n", PS4.Battery());
        //  if (PS4.Down()) Serial.print("Down Button = ");
        //if (PS4.Down()) Serial.println(down_button);
        //if (PS4.Up()) Serial.print("Up Button = ");
        //if (PS4.Up()) Serial.println(up_button);
         // Serial.print("button_pos ");
         //Serial.println(button_pos);
         // Serial.print("Pot Val ");
         // Serial.print(potVal);
         // Serial.print("-- trimval ");
         // Serial.print(trimval);
         // Serial.print("-- upper lid ");
         // Serial.print(uplidpulse);
        //  Serial.print("-- lolid ");
         // Serial.print(lolidpulse);
         // Serial.print("-- xval ");
         // Serial.print(xval);
         // Serial.print("-- yval ");
         // Serial.print(yval);
         // Serial.print("-- switchval ");
         // Serial.println (switchval);
         //if (PS4.Charging()) Serial.println("The controller is charging");
          
  delay(50);

}
