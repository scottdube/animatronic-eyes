# animatronic-eyes

Will Cogley / Nilheim Mechatronics **Basic EyeMech** — two eyes (X/Y each) and
four eyelid servos on an Adafruit PCA9685 servo driver over I2C. Kit downloaded
May 2024. License is **CC BY-NC-SA 4.0** (`reference/License.html`), so the
kit files may be shared with attribution, non-commercially, under the same
license. Keep that in mind before this repo gets a public remote.

## State: the controller version is LOST

Scott had edited the sketch to drive the eyes from a **game controller**. That
version was not found anywhere. It likely lived only in an Arduino Cloud (web
editor) account that has since been closed. Searched 2026-09-24, all empty:

- every non-library `.ino` on this Mac (Spotlight), filtered for eye-servo code
  and for controller libraries (Bluepad32, PS3/PS4Controller, PS2X, XInput,
  USB Host, gamepad)
- the Google Drive mount walked with `find` (402 sketches, content-grepped for
  `lidpulse`/`lexpulse`/`Nilheim`) plus the Drive connector's full-text search
- Arduino IDE recent-sketches list, both sketchbooks, GitHub repos, both Trashes
- no Time Machine on this Mac

**Not searched:** the Mini, the 2014 MacBook Air, any Windows box. A compiled
board cannot give the source back.

`firmware/Low_Tier_Code/Low_Tier_Code.ino` is the surviving copy, from iCloud
Downloads (mtime 2024-05-16). It is the stock kit sketch plus three debug
`Serial.println` lines for `xval`/`yval`/`switchval`. The 2019 original is in
Google Drive `My Drive/#3D prints/basic_eyemech_download_package/`.

## The controller

`docs/controller.jpg`: a third-party **PS4 (DualShock 4) clone** with a "P4"
home button, a touchpad, and SHARE/OPTIONS. It's Bluetooth. The photo shows
what it is, not how it was paired or which board read it.

## Stock sketch pin map (the baseline to rebuild from)

| Input | Pin | Drives |
|---|---|---|
| Joystick X | A1 | servo 0, eye left/right (220–440) |
| Joystick Y | A0 | servo 1, eye up/down (250–500), and the lids track Y |
| Trim pot | A2 | lid opening offset |
| Button | D2 | HIGH = blink (lids closed: 2→400, 3→240, 4→240, 5→400) |

The PCA9685 runs at 60 Hz, with counts out of 4096. `reference/Servo numbers.png`
and `reference/Wiring.png` are the kit's servo numbering and wiring.

## Board and the rebuild

**ESP32-WROOM-32 DevKit** (micro-USB) on a breadboard. Scott confirmed the
module, and the board is in `docs/board.jpg`. It has Bluetooth Classic, so the
DS4 pairs to it directly with no USB Host Shield.

**Evidence for the lost version's library:** `~/Documents/Arduino/libraries/PS4Controller`
(pablomarquez76/PS4_Controller_Host v1.1.0, core-3.x compatible) was installed
**2025-05-30**. Hypothesis, not established: the lost sketch used it.

`firmware/EyeMech_PS4/EyeMech_PS4.ino` is the rebuild from 2026-09-24. It keeps
the kit's servo math unchanged, and the stick input is converted to the kit's
0..1023 range. Left stick = eyes, Cross = blink, D-pad up/down = lid trim.
Compiles clean against esp32 core 3.3.7 with the IDE's bundled arduino-cli:

    "/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli" \
      compile --fqbn esp32:esp32:esp32 --config-file ~/.arduinoIDE/arduino-cli.yaml firmware/EyeMech_PS4

**NOT yet flashed or run on the mechanism.** Unverified: axis directions
(`INVERT_X`/`INVERT_Y`), and whether the DS4 connects.

## Pairing trap

This library can only connect to the Bluetooth MAC the controller has stored.
It cannot put the controller into pairing mode. `PS4_HOST_MAC` empty = the
ESP32's own MAC. If the clone was paired to a PS4 console or another MAC, set
that MAC in the sketch, or rewrite the controller's stored MAC over USB with
sixaxispairer. Bluepad32 is the fallback if the clone refuses; it pairs DS4
clones without MAC games but needs its own board package.

## Open questions

- Is the PCA9685 wired to SDA 21 / SCL 22? The photo shows servo leads and
  jumpers but not where they land, so this is assumed.
