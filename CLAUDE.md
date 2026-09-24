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

## Open questions before rebuilding controller support

- Which board is in the mechanism? The stock kit is an Uno/Nano, which has no
  Bluetooth, so a DS4 needs either an ESP32 (Bluepad32) or a USB Host Shield.
- Is the kit's joystick board still attached, or was it removed?
