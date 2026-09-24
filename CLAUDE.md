# animatronic-eyes

Will Cogley / Nilheim Mechatronics **Basic EyeMech** — two eyes (X/Y each) and
four eyelid servos on an Adafruit PCA9685 servo driver over I2C. Kit downloaded
May 2024. License is **CC BY-NC-SA 4.0** (`reference/License.html`), so the
kit files may be shared with attribution, non-commercially, under the same
license. Keep that in mind before this repo gets a public remote.

**Remote: `scottdube/animatronic-eyes`, PRIVATE (created 2026-09-24). Keep it private:
the flash backup holds the controller link key, and the kit is NC-SA.**

## State: the controller version was lost, then RECOVERED 2026-09-24

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

**Best lead: `low_tier_code_mod_ps4.zip`**, about 2 KB, which Scott sent by
iMessage to **John** in May 2024. As of 2026-09-24 the Mac's copy fails
to download (iCloud copy expired), the iPhone doesn't have it, and it isn't in
Gmail or Drive. **John sent it back on 2026-09-24. It is now
`firmware/Low_Tier_Code_mod_ps4/`, and the zip is in `reference/original-zip/`.** The Mac's `~/Library/Messages` is behind Full Disk Access, so the
shell cannot read it. If the zip arrives, diff it against
`firmware/EyeMech_PS4`, and prefer flashing it over the rebuild.

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

**The lost version used PS4Controller: ESTABLISHED** from the flash backup
(below), which contains the library's L2CAP channel names `PS4-HIDC`/`PS4-HIDI`.
The installed copy is `~/Documents/Arduino/libraries/PS4Controller`
(pablomarquez76/PS4_Controller_Host v1.1.0), installed 2025-05-30.

## Flash backup of the working board: `backup/`

`board-flash-2026-09-24.bin` is the full 4 MB read of the board before anything
was flashed over it. It was verified with `verify-flash` (digest matched), and
`SHA256SUMS` is alongside. This is the only surviving copy of the lost sketch,
and only in compiled form. Chip: ESP32-D0WD-V3 rev 3.1, 4 MB, base MAC
d4:8a:fc:9e:7a:cc. Default partition table (app0/app1 at 0x10000/0x150000, nvs
at 0x9000). To restore it:

    ~/Library/Arduino15/packages/esp32/tools/esptool_py/5.1.0/esptool \
      --port /dev/cu.usbserial-0001 -b 115200 write-flash 0 backup/board-flash-2026-09-24.bin

**Second copy on Google Drive:** `My Drive/#3D prints/basic_eyemech_download_package/Board flash backup/`
(bin plus SHA256SUMS). The Drive API showed it server-side on 2026-09-24 at
4194304 bytes.

**Baud trap:** this board's CP2102 corrupts reads at 921600 and 460800. Use
115200 (a 4 MB read takes about 6.5 min).

**What the dump says:**
- NVS holds a Bluetooth bond with **8c:41:f2:a1:49:dc**, including a link key.
  That is the controller's own address.
- No MAC string appears anywhere in the app. So the lost sketch most likely
  called `PS4.begin()` with no argument, using the ESP32's own BT MAC. Inferred
  from an absence, so treat it as likely rather than proven.
- No web page or HTML strings. The Wi-Fi and SSID strings are IDF SmartConfig
  logs from the core, not the sketch.
- **The dump contains the pairing link key.** Do not push this repo to a public
  remote. The kit's NC-SA license is a second reason.

**Upload without "Erase All Flash".** A normal upload leaves NVS, and with it
the bond, intact. A full erase throws the pairing away.

`firmware/EyeMech_PS4/EyeMech_PS4.ino` is the rebuild from 2026-09-24. It keeps
the kit's servo math unchanged, and the stick input is converted to the kit's
0..1023 range. Left stick = eyes, Cross = blink, D-pad up/down = lid trim.
Compiles clean against esp32 core 3.3.7 with the IDE's bundled arduino-cli:

    "/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli" \
      compile --fqbn esp32:esp32:esp32 --config-file ~/.arduinoIDE/arduino-cli.yaml firmware/EyeMech_PS4

Flashed 2026-09-24 (EraseFlash=none, so the bond is kept). Boot prints "Bluetooth up".
**Controller connects: VERIFIED 2026-09-24 14:21.** Scott pressed P4, serial printed
`PS4 connected`, and both stick axes swept the full 4..1023 range. It paired with the
existing bond, with no re-pairing and no MAC set, so `PS4.begin()` on the ESP32's own MAC is right.
Scott confirmed on the mechanism the same day that stick direction, Cross blink and
D-pad trim all work as expected (serial also showed blink=1 at 14:30). **Reconnect without a power cycle: VERIFIED 2026-09-24 14:36.** After two
back-to-back flashes (RTS resets while the controller was connected), P4 alone did
not reconnect. Scott **held P4 about 10 s until the light went out, then pressed P4
once**, and serial showed `PS4 connected` with the light bar solid. The eyes' power was not touched.

**To reconnect: hold P4 about 10 s until the light goes out, then press P4.** A
DS4 has no off button, and Scott didn't know this trick until today.

Added the same day at Scott's request: the **right stick drives the eyes too** (per axis,
whichever stick is pushed further wins; summing them was rejected because it would
double the throw), and **`Y_PARK`** rests the eyes below mechanical centre, 60 of 1023 at first, then 120, then 180 as Scott asked for lower each time
to start. Each half of the stick travel is stretched so both ends are still
reached, which is why the offset isn't simply subtracted, since that would clip the top.

**Core 3.x trap:** esp32 core 3.3.7 frees Bluetooth memory at boot unless
`btInUse()` returns true, and PS4Controller doesn't set it. Without
`extern "C" bool btInUse() { return true; }` in the sketch, `PS4.begin()` fails.
Any sketch using this library that is built on core 3.x needs that line.

## The original (John's copy) vs the backup

The backup matches this source: it contains the sketch's `Ready.` string, and it
was **built on esp32 core 2.0.16 (IDF v4.4.7)**, per the core paths and the
IDF version string in the dump. This Mac now has core 3.3.7 only. Differences
from the rebuild:
- `PS4.begin()` has no argument, which confirms the inference above.
- **Square** blinks, not Cross.
- The stick maps straight to the servos (-127..127). X runs 180–440 (the kit uses 220–440),
  and the upper lid runs 250–400 (the kit uses 280). `servoPos`/`servoPos1` in `notify()` are
  computed but never used.
- D-pad up/down steps the lid trim by 25 per 50 ms loop while held, over -50..50, starting at 50.
- There is no `isConnected()` guard, so on disconnect the eyes hold their last position.

## Pairing trap

This library can only connect to the Bluetooth MAC the controller has stored.
It cannot put the controller into pairing mode. `PS4_HOST_MAC` empty = the
ESP32's own MAC. If the clone was paired to a PS4 console or another MAC, set
that MAC in the sketch, or rewrite the controller's stored MAC over USB with
sixaxispairer. Bluepad32 is the fallback if the clone refuses; it pairs DS4
clones without MAC games but needs its own board package.

## Observed 2026-09-24: lost control after the backup, and a power cycle fixed it

After the esptool read and verify sessions, which each end in a hard reset
over RTS, Scott switched the controller off, then pressed P4 to turn it back
on. The eyes no longer responded. A power cycle of the eyes restored control.
**The flash was not changed:** verify-flash matched the backup byte for byte
after the read. Cause NOT established. Candidates: (a) the board came back from
an esptool reset without BT ready; (b) the old firmware does not survive a
controller off/on without an ESP32 restart, a known PS4-esp32 weakness;
(c) **hypothesis, likeliest:** the controller was never actually off. Scott said later that
day he didn't know how to turn it off, so pressing P4 would not have restarted
its connection. The same symptom recurred on the rebuild after two quick resets, and the
hold-P4-10s-then-press sequence cleared it without a power cycle (see above).

## Open questions

- A PCA9685 is on the board (`docs/board-pca9685.jpg`, blue board with six
  servo leads and a 6-wire jumper to the ESP32). Whether the jumpers land on
  SDA 21 / SCL 22 is still unread, so that remains an assumption.

## Web settings + OTA (requested and built 2026-09-24)

Scott asked for Wi-Fi OTA plus a web settings page "just like the Info Orbs"
(`~/code/hot-info-orbs/firmware/src/core/ota`, `.../settings`). Scope he chose:
- **Park + lids:** eye rest height and left/right, and lid opening at power-up, as live sliders
- **Buttons:** which button blinks, and the trim step
- **Scenes:** the eyes run on their own for a set time, and later from a sensor trigger.
  This is its own subsystem, designed after OTA and settings.

Established so far: switching to the `min_spiffs` layout (2 × 1.875 MB app slots)
keeps NVS at 0x9000/0x5000, the same as `default`, so the bond survives the one USB flash
that changes the layout. Unlike the Orbs, settings must **apply live, with no restart**,
because a restart drops the controller. **The open risk is Wi-Fi + Classic BT on one
radio.** Spike it first: Wi-Fi on only, then check stick feel and reconnect.

**Step 1 MEASURED 2026-09-24 14:47–14:52** (serial, 'w' toggled Wi-Fi every 30 s
while connected, 5 min, Scott driving). Built with PartitionScheme=min_spiffs, and the
first USB flash of the new layout kept the bond: P4 reconnected with no re-pairing.
| | controller pkts/s mean (min) | loop/s |
|---|---|---|
| Wi-Fi on (192.168.30.211, RSSI -43) | 98.9 (44) | 112 |
| Wi-Fi off | 110.6 (57) | 112 |
There were 0 disconnects. Wi-Fi costs about 11% of controller packets, which still leaves about 100/s
against 60 Hz servo PWM. Both states dip for a second, so the minimums aren't Wi-Fi's.
**Free heap with Wi-Fi + BT up is only ~50.9 KB**, and that is the budget for
step 2: the sync WebServer and Update, with no LittleFS picture as the Orbs have. App is 1.605 MB, 81% of a slot.
Wi-Fi comes from `firmware/EyeMech_PS4/secrets.h` (git-ignored, copied from
the Orb's secrets.h fallback: SSID IoT). DNS name: hostname `eyemech`.

**Step 2 BUILT and tested 2026-09-24 (build da3d545).**
- Settings page: **http://192.168.30.211/**. Sliders apply live, and **Save** writes NVS
  namespace `eyes` (`EyeSettings.cpp`). The page also has Revert and Defaults.
  Status line: ● / ○ controller, ✎ unsaved / ✓ saved, then build, slot, IP and heap.
- OTA: `./build.sh ota` (curl to `/update`), or the `/update` page in a browser.
  Measured: the upload takes ~20 s and the eyes are back ~4 s later. Both directions were verified,
  app0→app1 (19b5791) and app1→app0 (da3d545), by the `slot` field on `/status`.
  **Any flash restarts the board and drops the controller: hold P4 ~10 s, then press P4.**
- `./build.sh usb` is the USB fallback, with EraseFlash=none.
- Rollback: `verifyRollbackLater()` returns true, and the app is marked valid once Wi-Fi joins,
  as on the Orbs. Whether this core's bootloader really rolls back is **unverified**.
- **No OTA_PASSWORD** (same as the Orbs). Anyone on the IoT network can change settings or
  flash. Define `OTA_PASSWORD` in `secrets.h` to require login as `admin`.
- Heap with Wi-Fi + BT + server: ~44.7 KB free, 43.6 KB during a request.
  App 1.667 MB = 84% of a slot.
- `eyemech.internal` did NOT resolve at first boot (curl 000); use the IP.
  **192.168.30.211 is now a UniFi fixed IP** (Scott, 2026-09-24).

**Step 3, scenes: BUILT 2026-09-24 (build 9d59dd5, app1).** Spec:
`docs/superpowers/specs/2026-09-24-eyemech-scenes-design.md`. `Scenes.cpp` decides who
drives; every source emits the controller's Frame, and the kit math is the only path to
the servos. Triangle = idle, Circle = play, Share = record; sticks/blink/D-pad take over.
Page has scene buttons, the mode in words + glyph, and sliders for lids, idle and radar.
`POST /scene?cmd=idle|play|record|stop|sleep|wake`, `POST /presence?state=on|off`.
- Settings Scott had saved survived the new table layout (parkY 270, trimStep 10).
- **Verified over HTTP, no controller:** auto idle started ~20 s after boot; sleep, wake,
  idle and stop all switch mode; play and record refuse (409) with no recording / no controller;
  presence=on right after a page command is skipped by design (operator active).
- **Not yet verified:** how idle LOOKS (Scott), the lid sliders on the mechanism (watch for
  a straining servo below 280), record/replay with the controller, the light bar colours,
  and the radar (HA package not written yet).
- Deviation from spec: `emptyAction=rest` holds rest until presence/takeover/command.
  Without that, automatic idle restarts at once (already unattended) and "rest" means nothing.
- Heap after boot with the scenes code: 43.7 KB free. App 1.678 MB = 85% of a slot.
