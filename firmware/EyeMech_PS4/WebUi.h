#pragma once
// http://<eyemech>/        settings page: live sliders, Save / Revert / Defaults
// http://<eyemech>/update  firmware upload (OTA). The board restarts when done,
//                          which drops the controller: hold P4 ~10 s, then press P4.
// Modelled on hot-info-orbs' OtaUpdater + SettingsPage, minus the boot picture
// (heap is ~51 KB with Wi-Fi + Bluetooth up). Set OTA_PASSWORD in secrets.h to
// require a login (user "admin") for both pages.
#include <Arduino.h>

void webBegin();   // once, from setup(), after Wi-Fi has been started
void webHandle();  // every loop

// Implemented in the sketch
String eyeStatusJson();                     // live state for the page's status line
String pcaRegsJson();                       // GET /pca: PCA9685 register dump
void setPcaTest(int8_t t);                  // POST /pcatest: 1 full-on, -1 full-off, 0 run
void applyLiveSetting(const String &key);   // a setting just changed in RAM
