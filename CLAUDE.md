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

**Idle fix 2026-09-24 (build 6ca51ce).** Scott: pupils never visible while idling, too high.
Cause: glances were even in stick units, and with parkY 270 the stick's upper half spans
781 units vs 242 below, so idle looked up ~3x further than down. Now picked in 0..1023
units around rest. Measured after the fix over /status (80 samples, 0.3 s apart): y 209–352,
mean 260, around rest 242; x 320–568, mean 481, around 512. The park sliders are now
labelled **Pupil centre**, and dragging one stops idle so the centre can be set by eye.

**The up/down servo horn fell off (2026-09-24).** The eyes are held at kit centre (x 512,
y 512 = servo 1 pulse 375) with idleMode 0, parkY 0, parkX 0 set live and NOT saved (NVS
still has parkY 270 and idleMode 1) so Scott can re-seat it. **Hypothesis, untested:** a slipping horn
could be why "park lower" was asked for three times and why the pupils read high. Re-set
the pupil centre after the horn is back on, before trusting parkY 270.

**Lid horns re-seated 2026-09-24.** After the up/down horn was refitted, the right eye's lids read
"180 out" and each of the four lids sat differently. Held all lids at the kit's closed command
(Sleep: servo 2=400, 3=240, 4=240, 5=400), and Scott re-seated all four horns so each lid is just
closed there. That is now the mechanical reference for the lids. Open position not yet checked.

**Nothing moved after the horn work (2026-09-24).** After Wake, no servo moved or buzzed while
`/status` showed the controller connected and the loop running. **Hypothesis, untested:** the
PCA9685 lost logic power (a bumped jumper) and reset into sleep; the sketch configured it only in
setup(). Build 5688032 reads the prescaler back every second and re-inits on a mismatch; `/status`
now has `pca`, `pcaPrescale` (101 = 60 Hz; 30 = power-on default) and `pcaResets`. First boot of it:
pca true, prescale 101. If servos still don't move with pca true, it is servo V+ (not visible to software).
**Outcome:** still nothing after the re-init with pca true, so the PCA9685 hypothesis is **ruled out**
for this event. **Scott pulled the power and reapplied it, and everything moved again.** The fault was on
the power side. Whether the servo supply latched off (e.g. overcurrent from a stalled servo while the horn was
off) is NOT established. **Consequence:** the servos were limp during the lid-horn re-seat above, so the
"180 out" lids and the four different lid positions were unpowered servos, not a mechanical fault, and that
re-seat is void. Redone with all six servos holding in Sleep at kit centre: servo 0 = 330
(x 512), servo 1 = 375 (y 512), lids closed 2=400, 3=240, 4=240, 5=400.
**Lesson: before re-seating a horn, check the servo is holding (push the arm and feel it resist).**

**After the re-seat (photo 2026-09-24):** at full open (trim 40, eyes at kit centre) the top lids still
cover about half of each eye: the kit opens the top lid only 400 → 340 there. Stepping `lidMin` down
live, not saved: 265 first (top lid 325), then toward 250 as long as nothing strains.
Stepped live with Scott watching, no buzz at any step: lidMin 265 → 250 → 240 (range widened to
200 in firmware) → 230 → 220 → 210 → 200. Added `lowLidMax` (400 kit .. 480) and set 480 to match.
Photo at lidMin 200 / lowLidMax 480: all four lids fully clear of the eye, pupils visible. NOT saved yet.
Closed check (photo): both eyes seal with no gap; the right eye (as viewed) lower lid rides slightly over the upper.
- **Ruled out 2026-09-24:** 'stuck /set after an OTA restart' as the cause of Scott's dead sliders: he had already reloaded, and it still does nothing (the 3 s timeout fix stays; it is harmless).

**Saved 2026-09-24 16:21 after re-seating every horn:** pupil centre parkY 0, parkX -75 (Scott, by eye),
lidMin 200, lowLidMax 480, idleMode 1. The old parkY 270 is gone: it was compensating for a slipping horn.
**Dead sliders, cause NOT established.** Scott's page (reloaded) did nothing for a while, while `/set`
from curl and a fresh page in my browser moved the eyes. It worked once my page was closed, but it had
started failing before mine was opened, and parkX 15 from his page had arrived earlier. Suspect the sync
WebServer (one client at a time) and several open pages polling /status every 2 s. Untested.
- **OTA can fail with `curl: (56) Connection reset by peer`** mid-upload: 2 of the last 7 uploads
  (2026-09-24). The old build keeps running (nothing is half-written), and an immediate retry
  succeeded both times. Cause not established; free heap was ~34–40 KB both times vs ~43 KB on
  clean boots. `./build.sh ota` does not retry. Check `build` in `/status` after every OTA.

## Up/down servo RUNAWAY during idle (reported 2026-09-24, OPEN)

Scott, twice: while a scene (idle) ran, the bottom-centre servo (servo 1, eye up/down) swung
the horn ~180° the wrong way, "up over the top" instead of small moves low down, and kept running
until he cut power. Once the horn popped off and the motor ran on. The first horn loss
earlier the same day was probably the same event. Idle stopped and idleMode 0 set live (unsaved) at his "stop".
**Measured:** `/status` after it: same boot as the last OTA (unsaved trim 5 still live), `pcaResets` 0,
so the PCA9685 did not reset in this boot. **Software bounds:** every source reaches servo 1
only through `map(yval,0,1023,250,500)`, and yval is bounded 0..1023 (stick constrained ±128), so
commanded pulses stay in the kit's 1.0–2.0 ms. Idle's vertical travel (±120 around 512 → pulses ~346–404) is
SMALLER than full stick. A 1–2 ms pulse cannot make a servo spin continuously; that means the
servo can't reach its target (linkage jammed or past a stop, or gears/pot slipping).
**Hypotheses, none tested:** (a) the up/down linkage goes over-centre at the edge of travel since
the horn was re-seated, then jams and stalls; (b) supply current limit/brownout under idle's fast
moves (the bench supply may be current-limited; the dead-servo event earlier fits a supply in protection);
(c) a damaged servo 1 after the first horn loss.
**Cause, strong hypothesis (Scott, 2026-09-24): the six servos run off the ESP32 DevKit's 5 V pin**, i.e.
USB power through the board's diode, with no separate servo supply. SG90s draw ~100–250 mA moving and
~650+ mA stalled each; idle's fast glances plus 4-lid blinks can ask for well over 1 A at once. That fits
all three symptoms: the rail sagging makes the servos erratic (runaway); a USB port or the board's fuse tripping
leaves the ESP32 up but no servo moving until it is unplugged and plugged back in (the "nothing moves" event,
`pca` still true); and controller driving is gentler, so it didn't show. **Fix:** a separate 5.0 V supply,
≥2.5 A, into the PCA9685 V+ screw terminal. Take the ESP32 5 V off the header's V+ (or the bench supply
back-feeds USB), keep GND common. Not yet done or tested.
**After the bench-supply rewire (2026-09-24):** `/status` pca false, pcaResets 103 and climbing (one per second): the PCA9685 stopped answering I2C at the rewire. So the logic side (VCC 3.3 V, SDA, SCL or GND on the header) was disturbed, not just V+. The watchdog caught it on its first real outing. Idle stopped again until it answers.
VCC header wire was loose (Scott). Re-seated: pca true, the watchdog re-initialised the chip on its own (pcaResets stopped at 263). Idle restarted on the bench supply with Scott watching.
Idle on the bench supply ran clean (Scott). Supply display: usually peaks ~300 mA, high 400s on
back-to-back blinks. A supply's panel meter averages, so real spikes are higher; that is right at
the ~500 mA a USB port gives, which is consistent with (not proof of) the USB-power cause.
Saved 2026-09-24 ~16:40: idleMode 1, bootTrim 5.

## Lid presets tuned live with Scott (2026-09-24, NOT saved yet)
Four presets (Wide/Normal/Squint/Closed, % open); the D-pad and idle pick between them. Scott approved:
**lidNormal 60** (75 = the old trim 5 read too wide; he saw 75, then 60) and **lowLidCurve 100** (bottoms
at the same % as the tops; 50 left the bottoms too open at 60). Squint shown at the default 35 (photo): pupils
about half covered, reads as squint; awaiting his call. Wide not yet reviewed. idleMode is 0 live while
tuning: set it back to 1 BEFORE Save, or Save stores idle off.
**Squint photo: the eye on Scott's right (viewer's right) is more open than the other, top AND bottom lid.**
Measured from the photo only. Known contributor, not an established cause: the kit's closed pulses are not
mirrors (2=400/4=240, 3=240/5=400), and the open side mirrors with 680-x, so pulse travel from closed differs
per servo (2: 400→200 = 200, 4: 240→480 = 240; 3: 240→480 = 240, 5: 400→200 = 200). That predicts ONE lid
per eye more open, not both lids of one eye, so it does not explain the photo alone. Linkage/horn spline
offsets are the other candidate.
**Measured (Scott, calipers, squint 35):** one eye 10.5 mm open, the other 7.5 mm. Added `lidBalance` -40..40
(build 36c52da-dirty = this commit): scales one eye's lid travel from closed (− = servos 2+3, + = servos 4+5),
so the closed seal is kept. Started at +29 (7.5/10.5 = 71%). Which physical eye is servos 4+5: pending Scott.
**Saved before the OTA** (an OTA restart drops live values): lidNormal 60, lowLidCurve 100 — and idleMode **0**
(tuning). Set idleMode 1 and Save again when tuning ends. Rejected equalising the four servos' pulse travel:
at wide it would push servo 5 to ~160, past the range checked for buzz.
**Balanced (Scott, 2026-09-24):** lidBalance +29 plus a small nudge of one horn: "they're good now". Saved.
Which eye is servos 4+5 was not asked; the slider still reads −/+ not left/right.
**Horns settle (Scott):** after re-seating, a horn needs to work a little, then realign it, and it lands about
where it should. So a lid mismatch right after a re-seat is partly horn settling, not only software; run the
lids a while before trimming lidBalance again.
**Wide wider (Scott, 2026-09-24):** at lidMin 200 / lowLidMax 480 he wanted more. Those were the old slider
ends, not a found stop, so the ranges now reach 160 / 520 (build 4880f6d). Stepping live, not saved: 190 / 490 first.
Caveat: lidBalance +29 scales wide too, so the balanced eye opens only 71% of its travel at wide.
190/490: no buzz (Scott). Stepped to 180/500.
**Presets done and SAVED 2026-09-24:** wide at lidMin 180 / lowLidMax 500 (no buzz, "that's good"), normal 60,
squint 35, closed 0, bottoms curve 100, lidBalance +29, idleMode back to 1 (automatic).
**Horns re-set at wide (Scott, after the save):** matched the horns with the eyes at wide; normal then no
longer matches. Expected, not a new fault: lidBalance +29 scales one eye's whole travel from closed, so that
eye is at 71% at wide and 43% at normal while the other is at 100% / 60%. A horn offset set at one point cannot
match at the others while the balance scales. Proposed: lidBalance 0, horns seated at ONE reference (closed),
then check normal and wide.
**Eye mapping, CORRECTED:** servos 4+5 = the eye on the VIEWER'S LEFT (Scott's left facing the eyes; the
robot's right eye); servos 2+3 = viewer's right. Measured: that eye got wider the moment lidBalance went +29 → 0
(Scott watching). My first reading from the normal photo said the opposite and was WRONG: a photo taken after
horn moves compares two uncontrolled eyes, it does not show which servo pair the balance acts on. Consequence:
the original squint fix (+29) shrank the viewer's-LEFT eye, but the too-open eye was the viewer's RIGHT, so the
balance was correcting the wrong eye and Scott's horn nudges were compensating for it.
Scott: "Horns are aligned" — arrived as balance went to 0; which balance he aligned against not yet confirmed.
Normal photo at lidBalance +15: viewer's-left eye still far wider than the right (top lid well clear of the pupil). Stepped to +30.
+30: still more wanted (Scott). Stepped to +40, the slider end.
+40 (range end): still more wanted. A >40% scale points at a horn seated open, not travel. Showing closed to check whether the viewer's-left eye seals.
**Closed photo at balance +40:** viewer's-right eye sealed; viewer's-LEFT eye open a slit, pupil visible. Scott
re-seated horns to seal and named the real problem: **each lid has two ends to fit (closed, wide) and only one
adjustment (the horn), so fixing one end moves the other** — back and forth. A spline step (~17° on an SG90) is
also too coarse. lidBalance (one scale per eye) cannot fix it either. Proposed: per-servo closed + open trims.
Per-lid trims live on de940f3 (all 0). idleMode 0 live again for tuning; saved value 1.
Preset buttons on the page (3229ac7). Closed trims saved before the OTA: botLClosed -14 (Scott), rest 0.
**Per-preset lid trims (build 1033ac6):** Scott: after closed + wide were trimmed, squint still showed the
viewer's-left eye wider, so end-trims plus interpolation don't fit the middle (nonlinear linkage). Now 16 trims,
c/s/n/w × TopL/BotL/TopR/BotR; the page's preset buttons select which preset the four trim sliders edit.
Between presets the trim blends by lid %. Migrated botLClosed -14 → cBotL -14 and saved (idleMode 1 saved, 0 live).
Page JS not exercised by me (no browser: my open tab coincided with the dead-slider episode); Scott's first use is the test.
**faa5248 (Stop holds, timed run ends, `held` in /status) is committed but NOT on the eyes.** 2026-09-25 the
OTA could not reach them: laptop on 192.168.1.203, gateway 192.168.1.1 answered "Destination Host
Unreachable" for 192.168.30.211 (eyes powered off, or off Wi-Fi; not established). Eyes still run 1033ac6.
Deploy with `./build.sh ota` from the shop, then check `build` in /status.
**Why the eyes were off 2026-09-25 (Scott):** he powered them down because they "were running consistently",
idling nonstop. How idle got back on after idleMode 0 was set live is not established (a power cycle would do
it: saved idleMode is 1). Design gap either way: automatic idle has no end without the radar. Only a bench-empty
report ends it (emptyAction sleep), and the HA package that sends presence is not written. So on a plain
power-up it idles 24/7.

## How Scott wants to enjoy them (stated 2026-09-25) — the requirement the scenes must meet
Everyday: walk into the lab → wait **30 s** (setting) → wake and do its thing for **2–3 min** (setting) → go to
sleep. **Not running constantly while he's in the lab: the cheap servos are loud and get annoying.** Sometimes
he wants a longer run, as an option — maybe a Home Assistant voice command for "extended play".
This replaces "automatic idle whenever unattended", which ran 24/7 and got the eyes powered off.
Re-trigger (Scott): BOTH coming back after the lab has been empty a while AND a periodic show while he's there.
**Show cycle built 2026-09-25** (spec revision in docs/superpowers/specs/2026-09-24-eyemech-scenes-design.md).
Supersedes faa5248's Stop/hold fixes (holdRest removed: nothing automatic runs unprompted now). NOT deployed:
eyes are off. On deploy, check: power-up → show at +30 s → sleep; quiet sleep lids don't sag; /presence on/off.
**Power, 2026-09-25:** Scott asked to go back to servos on the ESP32 5 V pin. Advised against: on that pin
the eyes had two runaways and a "nothing moves" dropout; on the bench supply, none. Meter peaks already reached
the high 400s mA (a panel meter averages, so real spikes are higher) against a USB port's ~500 mA through
the board's diode. Consistent with USB power as the cause, not proof. Suggested: one 5 V ≥3 A adapter into the
PCA9685 V+ terminal, feeding the ESP32 5 V pin from that same rail (a single plug, no bench PSU). The trap:
don't have USB plugged in as well, or two supplies back-feed; flash by OTA.
HA package sln-ha-config f71964f pulled to the NUC 2026-09-25; `ha core check` passes (login shell needed). Not loaded: needs an HA restart, waiting on Scott's OK. Voice + presence unverified.
**Deployed 2026-09-25:** firmware 7a72ac6 on the eyes (emptyMins 5 saved); the power-up show was scheduled
(nextShow 16 s). HA restarted with Scott's OK. **Measured over /status right after:** present true (the HA
presence automation reaches the eyes), show running with showLeft counting down, nextShow ~3595 s (periodic,
showEvery 60). Show ended into mode sleep on time (showLeft -1, pca true, no resets). Quiet-sleep lids stay
shut (Scott). Voice "eyes extended play" and "eyes sleep" both work (Scott, 2026-09-25).
**Trims saved by Scott 2026-09-25** (read back from NVS after the 33d1c54 OTA restart; `dirty` was false just
before the OTA, so nothing unsaved was lost): closed BotL -14; squint TopL -9 BotL -43; normal TopL -14 BotL -41;
wide TopL 23 BotL 33 BotR 33; all others 0. Save button now answers on the button (33d1c54), not yet pressed by Scott.
**Eye X direction MEASURED 2026-09-25:** x 662 (parkX 150, above center) = the eyes look to HIS left (Scott,
asked "his left or his right?", answered "left"). So higher xval / servo 0 pulse = his left.
**Perspective rule (Scott, 2026-09-25): left/right always means the ANIMATRON'S left/right**, like up/down,
so it survives mounting him in a robot. His left eye = servos 2+3 (viewer's right); his right eye = servos 4+5.
**Show set pieces + his-perspective labels (build d87a7ef, 2026-09-25):** wake look (wide, far to his left, 2.5 s)
on a show that starts from sleep; slow squint about once a minute (wide → squint over 3 s, one 6 s sweep his left →
his right → center); winks, random eye, every 25–60 s. Trims renamed to his own left/right (cLTop.. ; L = servos
2+3) and migrated from NVS on first boot, verified by /values: old cTopL→cRTop etc. Closed read cLBot 43 /
cRBot -21, not the -14 read earlier: Scott re-trimmed closed in between. **This OTA went out WITHOUT a dirty
check**, so whether anything unsaved was lost is unknown; `./build.sh ota` now refuses while /values is dirty.
Not yet seen by Scott: the three set pieces, and the relabeled page.
**Center calibration (build 5ebecee, 2026-09-25):** parkX -75 migrated to `xCenter` -16 (pulse counts, applied at
servo 0), parkX now 0 = true center; verified by /values and /status x 512 at rest. Travel is now ±110 pulses
about center (was +126 his left / −94 his right), so his right end reaches pulse 204, 16 past the kit's 220:
**not yet checked for a stop.** Page has look-test buttons (full his left / right / up / down / center, held
until anything else happens). Also fixed: d87a7ef's trim rename broke the trim sliders' preset switching.
**xCenter -33 saved (Scott, by eye, 2026-09-25)**, not the migrated -16: the old parkX -75 was not true center.
So his right end now reaches pulse 220+110-33 = 297-110 = 187 and his left 407: re-check both with the look test.
**yCenter added (build 9bcf632):** servo 1 only (+ = up); lids follow commanded gaze, so lid trims stay valid. 0 until Scott sets it.
**Checked (Scott, 2026-09-25):** full look to his right at xCenter -33 (pulse 187) does not strain. Saved with
yCenter 0 (either level already or not moved; not asked). His left (407), up and down not reported.
**Up strains a little at full travel (Scott, 2026-09-25); left, right, down don't.** Added `upMax` (bf5ab9b, servo 1
pulse at full up, kit 500, scales the upper half). Set 490 live and held lookU; by the next read upMax was back to
500 with nothing unsaved (Revert?), so 490 went untested. **Scott settled on upMax "495": no strain, saved; NVS reads 494 (the slider steps by 2 from 420).** Page 882589a: all calibration in one section.
xCenter stays -33 by design: it is the servo's offset; parkX is the everyday knob that reads 0.
**Service + set pieces (build 97339ba, 2026-09-25).** 🔧 Service verified over HTTP: mode service, lid 0 (closed
preset), a show refused with 409, look test still holds (x 1023), nextShow -1, 🔧 again → rest. **Not tested:**
the NVS flag surviving a power cycle. Set pieces now rotate every 30–50 s (slow squint, eye roll 1.3 s eased,
circle at 95% of travel 2.4 s); not yet watched by Scott. First upload of 97339ba failed with curl (55) broken
pipe; the retry took (same intermittent failure as before).
**Horn refit method (advised 2026-09-25):** 🔧 Service, paint-pen line horn→case, refit on the tooth that lines
up under the same command, then check Closed + Wide. Screws snug with servos holding; no threadlocker (cracks
plastic). A replacement servo needs its own recalibration.
**Why the controller needs hold-P4-10 s after a flash (Scott asked 2026-09-25):** the ESP32 restart kills the
link but the DS4 clone doesn't notice promptly and has no off button; this library can't call the controller,
the controller must call it, and a DS4 only does that on power-up. Holding P4 ~10 s forces it off; the next
press is a fresh power-up that calls the stored host. **Hypothesis, untested:** waiting until the light bar goes
dark by itself (a DS4 gives up after a while) and then one press would work too.
**Rail monitor (build affbc83, 2026-09-25):** /status `rail`, `railMin`, `railMax`, `railDips` (see baseline below), `reset`
(last restart reason); page line under the mode. Needs a 10k/10k divider, ESP32 5 V pin → GPIO34 → GND: NOT
wired yet (reads 284 mV floating; the page says "not wired"). Heap after boot 37.7 KB (the task stack is 3 KB).
**Supply evidence so far:** the bench PSU panel never showed near 1 A (Scott; peaks high 400s mA). A panel meter
averages over ~0.25–0.5 s, so it can't see ms spikes. The 2–4 A spike figure I gave is an ESTIMATE, not measured;
the PPK2 (Scott has one, and a scope) on ONE servo can measure a real SG90 peak/stall within its 1 A limit.
**Rail baseline, divider wired (2026-09-25).** ESP32 on USB; servos on the bench PSU (Scott confirmed:
the only supply they have run on so far). So this baseline measures the ESP32's own USB feed with the servo
current on a separate path; it says nothing yet about servos sharing the USB path. Measured on the ESP32 5 V pin:
- Level ~4.47–4.49 V, flat through a show and in sleep alike. That is USB 5 V minus the board's diode: the
  pin sits ~0.5 V under 5 V on USB, so the old absolute 4.6 V dip threshold fired forever (dips stuck at 1).
- Single samples spread 3.90–4.77 V in a show and 3.95–4.77 V in sleep with the servos drawing nothing: ADC
  noise, ±~0.4 V per sample. Mins of single samples are meaningless on this ADC.
- 16-sample (~1 ms) averages, build after c5cfdcd: min 4.20 V in a show (100 s) vs 4.20 V asleep (60 s).
  **No servo sag is resolvable by the on-board ADC with this supply.** Sleep still dips ~0.27 V below level,
  cause unknown (ADC, or real Wi-Fi TX load on the USB cable; the scope settles it).
- Monitor now tracks 1 ms averages against a ~2 s running level; a dip = 0.4 V below level (clears the 0.27 V
  no-load floor). The show-from-GET mistake: /scene is POST only; a GET returns "not found".
**Next:** repeat with the servos on the ESP32 5 V pin (USB only); a real sag shows as the level dropping or dips
counting. Scope on the pin is the tie-breaker for anything under ~0.3 V.

## Eyeball CAD (2026-09-25)
The eyeball STL is rebuilt as a native Fusion solid ("Eye Ball native" in the "Eye model"
document); decoded dimensions and the check against the mesh are in `docs/eyeball-cad.md`.
**First USB-only run (servos on the ESP32 5 V pin, 2026-09-25): Scott saw NO show.** Measured: last reset before
the run was `brownout` (Scott was rewiring). Firmware ran the show (mode idle) 0–140 s with the rail flat at
4.45–4.48 V, min 4.34 V, 0 dips: no sign of servo load at all. At ~145 s the board restarted (`power-on`),
min 3.73 V. A lookL right after gave a 0.42 V dip (1 count) within 2 s. Cause of "no show" NOT established:
hypotheses are servos unpowered during the show (the flat rail fits) or the show running in a still phase.
**USB-only show, after Scott reset the ESP (2026-09-25) — measured, servos on the ESP32 5 V pin:** show ran
150 s with no restart. Rail level sagged from 4.47 V to ~4.40–4.41 V while moving (one 2 s read at 3.94 V);
1 ms averages bottomed at **3.61 V**; **95 sags of >0.4 V** in 150 s. Bench-PSU baseline for comparison:
min 4.20 V, 0 sags in 100 s. So sharing the USB path does sag the rail by ~0.85 V in ms bursts; it did not
brown the ESP out this run. What it means for margin (the LDO's dropout off a 3.6 V input, instantaneous
dips deeper than a 1 ms average) is not measured — the scope on the 5 V pin is the instrument for that.
Scott (2026-09-25): the eyes twitch and jump all the time on EITHER supply — it's how this build moves — so
visible motion can't tell the supplies apart. Next instrument: scope, CH1 ESP32 5 V pin, CH2 ESP32 3V3 pin.
**Scope, first capture (DHO914, 2026-09-25, eyes ASLEEP, not in a show):** CH1 5 V pin sits ~4.5 V (agrees
with the ADC's 4.47), CH2 3V3 ~3.35 V. Both carry µs needles in both directions (CH1 ~±0.2 V, CH2 up to
~+0.27/-0.19 V) at 1 ms/div, 500 kSa/s; no broad sag in that 10 ms window. Bidirectional µs needles read as
switching/probe-ground pickup, not supply sag — hypothesis. Between the USB show ending and this capture
(sleep, probes going on) the counter went 95→109 sags and min 3.61→3.50 V: unattributed (probing?).
**Scope, during the show (same settings, 1 ms/div, edge trigger 3.97 V, STOPped by Scott):** still only µs
needles; the deepest pair coincide (CH1 to ~4.05 V, CH2 to ~2.98 V, same instant), no broad dip in the 10 ms
shown. Meanwhile the ADC logged min **3.37 V** and 41 sags in the first 60 s of that show. Conflict unresolved:
a 16-sample average that low needs a dip wider than one needle — either wide dips exist that this capture
missed (an edge trigger at 3.97 V fires on needles, so the screen shows the last needle), or the ADC itself is
disturbed. The burst length ("~1 ms" above) was NEVER timed — likely shorter. Next: pulse-width trigger.
That scope-show run finished: 150 s, 90 sags, ADC min 3.37 V, no restart (reset still `power-on`).
**Pulse trigger (CH1 negative, >100 µs, 4.10 V, Normal) fired CONSTANTLY** — asleep and in a show alike —
while the 5 ms/div display (125 kSa/s, normal acquisition) showed CH1 flat ~4.5 V at the trigger point. The
ADC meanwhile counted ~1 sag/s in the show (81 in 105 s, min 3.34 V). So the trigger is firing on something
the decimated display doesn't draw. Not established what. Next: Noise Reject ON + Peak Detect + SINGLE.
**Peak Detect reveals it (5 ms/div, SINGLE, eyes asleep):** both rails carry a CONTINUOUS dense HF band, no
gaps — CH1 5 V pin ~4.1–5.0 V (±0.45 V around 4.5), CH2 3V3 ~3.0 V to off-screen above 3.7 V. The band's
bottom edge sits at the 4.10 V trigger level, which is why the pulse trigger chains constantly. So what the
ADC and every trigger have been seeing is HF noise, not load sag. Source NOT established: the USB charger's
switching ripple, probe-ground pickup, or the ESP32 itself. Next: tip shorted to its own ground at the ESP
GND (pickup test), then 10 µs/div to read the period.
**Pickup test (Scott, 2026-09-25):** CH1 tip clipped to its own ground at the ESP GND still shows the band.
A real rail can't appear between two points on the same ground, so the band is common-mode/pickup in the
scope setup, not ripple between 5 V and GND. Leading hypothesis (untested): the USB source's Y-cap (it was the BENCH supply's USB output, not a wall charger — Scott, later) couples
switching + mains noise onto its output ground, and the earthed scope's probe grounds give it a loop. Test:
run the ESP from a floating source (power bank, or laptop on battery) — band gone = charger common-mode.
Until the band is gone the scope can't resolve a servo dip; 3 USB-only shows so far ran with no restart.
**Laptop USB (floating source), 2026-09-25:** the HF band is gone at rest (charger common-mode confirmed as the
band's source). Rail level now **4.73–4.79 V** (charger gave 4.46). During a show the pulse trigger (neg,
>100 µs, 4.10 V) sat in WAIT: no dip wider than 100 µs reached 0.65 V below level. ADC still counts sags
(15 in 30 s, min 3.72 V) — so the ADC's sag counts are its own noise, not the rail.
**RUNAWAY on laptop USB (2026-09-25):** second laptop-powered show, trigger raised to 4.5 V (neg, >100 µs);
Scott saw a servo runaway and pulled the power. First runaway on the USB-only feed. Cause NOT established —
the scope's last capture (if it triggered) is the evidence; ask before theorizing.
**Runaway detail + 2 A wall wart (Scott, 2026-09-25):** on the 2nd laptop show the 4.5 V pulse trigger went
T'D→WAIT repeatedly (dips >0.27 V below level, >100 µs, were happening), then the runaway popped servo horns
off. The noisy source earlier was the bench supply's USB output. Now on a 2 A wall wart (still USB-only to the
5 V pin): scope looks much cleaner (Scott); rail 4.58 V, it booted into a show, so I put it in 🔧 Service to
stop motion while horns are refitted (service persists across restarts; toggle off on the page when done).
**2 A wall wart show (2026-09-25):** rail level 4.53–4.56 V by ADC, scope ~4.3–4.5 V — lower than laptop
USB (4.77). The 4.5 V pulse trigger sat in WAIT, but that is NOT a pass: the level was at/under 4.5 V, so a
negative pulse through 4.5 V can't complete. Needs the trigger ~0.25 V under the rail (4.2 V) to compare.
**Wall wart, trigger 4.50 V — 5 captures (2026-09-25), the answer:** the rail sits ~4.6 V between moves and
the trigger DID fire. Four captures show the rail climbing back slowly from ~4.2–4.3 V to ~4.6 V over 40+ ms
(recovery from a sustained sag, not needles); 3V3 steady at ~3.3 V in those. One capture
(`docs/scope/2026-09-25-wallwart-1V-step.jpg`): a ~0.3 V, <1 ms notch at the trigger, then a STEP from ~4.65 V
to **~3.65 V held >12 ms** (still low at screen end); **3V3 fell with it to ~2.95 V (band to ~2.87)** — the
regulator in dropout, below the ESP32's 3.0 V spec. Readings off photos: ±0.05 V.
**Verdict: USB → ESP32 5 V pin → PCA9685 V+ is NOT adequate for the servos** — measured 1 V / >10 ms sags on a
2 A wall wart, and a runaway on laptop USB. The bench PSU on V+ showed no sag (ADC 0 dips). Cause of the
runaway itself (servo electronics below their ~4.8 V rating?) remains hypothesis. Direction: feed V+ directly
from a 5 V supply on short thick leads with bulk capacitance at V+, not through the ESP32's USB path.
**PCA9685 bulk cap (Scott read a stock board, SLN A3-R8C1, 2026-09-25):** already 1000 µF 10 V at V+. Whether
the board in the eyes is the same one is assumed, not checked. Arithmetic: 1000 µF supplying ~1.5 A for 12 ms
would fall ΔV = I·t/C ≈ 18 V, so no practical cap rides through a sag that long — it's the source/path, not
missing capacitance. Retracts my earlier "add ≥1000 µF at V+": the fix is a direct, stiff 5 V feed to V+.
**Plan (Scott, 2026-09-25): LM2596 buck module → PCA9685 V+ AND ESP32 5 V pin** (same single-supply topology
advised earlier). Wire as a star from the buck's output terminals (separate leads to V+ and to the 5 V pin),
not daisy-chained through the PCA, so servo current doesn't drop across the ESP's feed. Set 5.0–5.1 V at the
buck before connecting. Standing trap still applies: USB unplugged while it's powered, flash by OTA. Verify
with the same scope setup: CH1 on the ESP 5 V pin, CH2 on 3V3, neg pulse >100 µs, level ~0.3 V under the
new rail. Module rating: chip 3 A; typical blue module ~2 A continuous without a heatsink.
**Smaller board (Scott asked 2026-09-25, space under the eye rack):** the PS4 controller needs CLASSIC
Bluetooth (Bluedroid BR/EDR), which only the original ESP32 has — the S3, C3, C6 and S2 don't, so the XIAO
ESP32-S3/C6 and S3 Superminis in stock are OUT. In stock and fitting: **Type-C D1 Mini ESP32 (WROOM-32), 2 @
SLN Electronics Bench RB-12** (http://192.168.50.10:8001/web/stock/item/340/), ~39×31 mm, same chip, so the
firmware carries over (SDA 21/SCL 22, rail ADC GPIO34 — pin exposure on this clone to confirm on the board).
A new board has a new BT MAC and no link key: re-pair the controller, or set PS4_HOST_MAC and copy NVS.
Bigger space win, not started: drop the PCA9685 and drive the 6 servos from the ESP32's LEDC PWM (16 channels);
trims are in PCA counts and would convert. LM2596 module ~43×21 mm; 14 in stock at A3-R7C2.
**Decision (Scott, 2026-09-25): keep the PCA9685, move to the D1 Mini ESP32** — just enough room under the
rack; servo wires routed back to it. Rejected dropping the PCA for simplicity.
**Settings snapshot before the board swap:** docs/settings/2026-09-25-devkit-values.json (from /values,
dirty false, no secrets in it). Note xCenter now -21 and yCenter 12 (were -33 / 0) — changed after the horn
refit, presumably by Scott; saved. The D1 Mini starts from defaults: restore from this file.
**Swap checklist:** USB-flash the D1 Mini (same FQBN/partition); new MAC → new DHCP IP, so move the
192.168.30.211 reservation (HA package and build.sh use it); restore settings; re-pair the controller.
**Controller onto the D1 Mini — plan (2026-09-25), not yet done:** make the new board BE the old host.
(1) Set `PS4_HOST_MAC` to the DevKit's BT MAC. Derived, not read: base d4:8a:fc:9e:7a:cc + 2 =
**d4:8a:fc:9e:7a:ce** (ESP32 BT = base+2) — confirm from the DevKit's boot line "ESP32 Bluetooth MAC" before
relying on it. (2) Copy the DevKit's NVS partition (0x9000, 0x5000 bytes on this partition scheme) to the D1
Mini over USB: that carries the link key for 8c:41:f2:a1:49:dc AND the current settings and service flag,
so the settings JSON becomes the fallback. Read it from the DevKit on the day, not from the 09-24 backup
(that one has old settings). Retire the DevKit: two hosts on one BT MAC would fight. Fallbacks in order:
MAC alone without the NVS copy (the common tutorial path), sixaxispairer over USB, Bluepad32.
**Buck input supply (2026-09-25):** Scott linked Amazon B0DKT5DH2K, a **12 V 2 A** 5.5×2.1 adapter (Scott;
I had read "3 A" from the search keywords in the URL, which was WRONG). 24 W against ~12 W needed: fine. Already in stock, no purchase
needed: **Power Adapter 12V 3A, model 1230** @ SLN/Assembly & Test (http://192.168.50.10:8001/web/stock/item/683/;
it sits beside the ZVS cooling-loop pump, so check it isn't that loop's supply; plug size not recorded), and
**5.5×2.1 female barrel pigtails, 12** @ SLN B0-R1C3 (http://192.168.50.10:8001/web/stock/item/802/) for the buck's IN+/IN−.
**Carrier PCB (Scott, 2026-09-25): one milled board carrying the D1 Mini, PCA9685 and LM2596, on standoffs into
the rack.** Outline from Scott's Fusion DXF, now `hardware/carrier/outline.dxf` (mm, AC1014): a 117.9 × 72.3 mm
plate, symmetric about x=0, with a 31.6 mm wide slot cut 39 mm down from the top edge (x −15.8..15.8, y −3.9..35.3),
so the usable area is two wings ~43 × 39 mm beside the slot and a full-width band ~33 mm tall along the bottom
(x ±40.6 at the bottom edge, ±56 higher up). Four 3.2 mm holes at (±49.5, 27.7) and (±28.5, −15.3) — M3, lands on
the 3.175 bit. The carrier IS the star wiring: buck OUT+ runs as separate traces to PCA V+ and to the D1 Mini VCC
pin, the 10k/10k rail divider and the bulk cap go on it. Rules from the pcb-design skill / fabrication guide:
single-sided B.Cu, 0.4/0.5 mm rules, 1.78 mm pads on header rows, NPTH under the ESP32 flash pins, 6.5 mm keepout
at each standoff hole, MountingHole symbols in the schematic.
**Inventory (2026-09-25):** project already exists — part #837 "Animatronic Eyes", build **BO-0010** — so the carrier's
parts go on that build, no twin. **Both D1 Minis at RB-12 (stock 340) are ALLOCATED to BO-0009 "Rat GDO - Florida
pair"**: 2 in stock, 0 available. The "2 in stock" note above was true and useless. Scott decides: release one
from BO-0009 or buy. The **12 V 3 A adapter (stock 683) is the shrink-fit kit's** (its notes say BO-0002), not free
either; the Amazon 12 V 2 A (B0DKT5DH2K) or another supply is needed. Free and allocatable: LM2596 (part #28, 14 @
A3-R7C2; the 15th at RB-25 has an unknown trimpot setting — check output before trusting any of them), barrel
pigtail (#1200, 12 @ B0-R1C3), 10k 1/4 W THT (#634, 28 in the EAONE kit), 100 nF (#645), 220 µF 10 V (#687, 15-value kit).
**Footprint sources:** `~/code/my-rat-ratgdo/kicad_files/D1 Mini - ESP32/` has an ESP32_mini footprint (40 pads, 4 rows
of 10 at x ±11.43/±13.97, 2.54 pitch, 1.4 mm pad / 0.8 drill → 0.29 mm annulus after snapping: passes the 0.25 gate but
redraw at 1.78) and a symbol whose pin NUMBERS are header positions (IO34 = pin 11, IO21/SDA = 27, IO22/SCL = 25,
VCC(USB) = 35, GND = 1/22/33, 3V3 = 16; SD0..CLK/CMD = 17,19,20,37,38,39,40 → NPTH). Its LM2596 footprint: four 2.54 mm
pads / 1.2 drill at (0,0) (17.6,0) (0,39.8) (17.6,39.8). Both are ratgdo's, NOT yet checked against the physical parts.
**Carrier Z zero is the COPPER, 0 typed in — pcbmill changed to match (2026-09-26, afternoon).** The blank was already
waxed to the MDF when it came time to zero. Scott: a used backer carries wax and never gives a true zero again; the
map is what every cut uses anyway, and the board bottom is a measured thickness below it. So pcbmill now defines Z0
as the copper (electrical touch, type 0): `verify` check 5 audits each hole's depth from (local map z − 
`blank.thickness_in`) and FAILS if the thickness is unset; probe header, run sheet, constants and web copy say so
(pcbmill commit "Z0 is the copper", issue 003 fixed, 43 tests green). **Blank thickness calipered by Scott: 0.80 mm =
0.0315 in**, which is what the job already carries. The probe program was regenerated with the new header and
redeployed to `~/gcode/eyes-carrier-v2_probe.ngc` (same 16 × 10 grid). Rejected the interim idea of typing the
thickness into TOUCH Z on a backer-referenced frame: it works, but it makes the operator encode the frame by hand
every job, which is how deskv1's map origin went unrecorded. With 0.0315 stock and zdrill −0.045 the holes land
0.0135 past the board bottom (need 0.003..0.030). **Two zeros, Scott's reminder:** (1) the PROBE (T99/H99) is zeroed on the copper, TOUCH Z = 0, and runs the map — this
zero only frames the map and does not have to be exact; (2) the FINAL zero is the V-bit itself, touched electrically
on the copper with a meter at the map's highest node, typing that node's z into TOUCH Z (`pcbmill touchoff` names the
node and two validation nodes). The cuts run on zero (2); zero (1) only has to be close enough that #7/#8 clear. Then
bring `probe-results.ngc` back, `probe-import`, `touchoff`.

**CORRECTION (2026-09-26, 14:30): the probe program is on the SHARE, `/Volumes/Tormach/gcode/eyes-carrier-v2_probe.ngc`.** Scott: "wrong gcode folder it is a mounted drive." `/Volumes/Tormach` is the `Tormach` share on the NAS BIG_BROTHER (192.168.1.200), mounted as sdube the whole time — the deskv1 files are in it. I had been probing the controller's own SMB share on 192.168.1.100, a different share, and never ran `mount`. `machine.gcode_dir` is back to the default `/Volumes/Tormach/gcode`, the file is deployed there (byte-identical to the laptop copy, which is deleted). The paragraph below is kept as the record of the wrong turn.

**Carrier probe program deployed to the LAPTOP, not the share (2026-09-26, 13:00) — WRONG, see above.** Scott: "use the gcode dir on this
laptop" — `machine.gcode_dir` is now `/Users/scottdube/gcode` (was `/Volumes/Tormach/gcode`, the value every job
carries by default) and `~/gcode/eyes-carrier-v2_probe.ngc` is there for him to carry over. Job `status`: probe map
NOT IMPORTED, every cutting artifact missing, verification never run — nothing but the probe program exists yet,
which is correct at this stage. What was learned trying the share first: the controller is **`tormachpcnc`
192.168.1.100**, Samba on Linux Mint, one share named **`gcode`** (guest, port 445 open, SSH closed); so a Finder
mount would land at `/Volumes/gcode`, not `/Volumes/Tormach/gcode`, and `mkdir /Volumes/Tormach` is denied even
outside the sandbox. `open smb://…` and `osascript mount volume` both put a dialog in front of Scott, which he
cancelled. Probe program facts for the console: 16 × 10 grid from X 0.05 / Y 0.05 step 0.38 / 0.42 in, Z safe
0.25 above WCS Z0, probe limit −0.05; **T99 / H99 (G43 H99), G54 Z0 on the COPPER** (superseded the backer zero the same afternoon, see above); it writes
`probe-results.ngc` beside itself (LOGOPEN bare name) and flushes every row, so an abort loses at most one row.
Then `pcbmill --job ~/PCBMill/eyes-carrier-v2 probe-import <path to probe-results.ngc>`.

**G54 X0 Y0 set (2026-09-26).** Scott: "x 0 y 0 are lower left hand corner set by eye with the vbit." That is the
frame the job expects — `blank.x0/y0 = 0, 0`, width 5.906 × height 3.937, so the lower-left corner of the copper IS
the origin, and the probe grid (X 0.05..5.75, Y 0.05..3.83) sits inside it with 0.05 in to spare on the low edges.
By-eye is fine for the carrier: the board has no features that reference the blank edge, and the pcb2gcode offsets
(x −6.8906, y 5.9405) center the board on the blank: the solver measured the copper/outline at X 0.632..5.274, Y 0.545..3.392, so **0.63 in margin left and right, 0.55 in top and bottom**, and the 1/8 outline cutter reaches 0.06 further (0.57 / 0.48 to the blank edge). A by-eye corner error of 1/8 in still leaves everything on copper. Remaining machine-side steps, in order:
Z0 on the copper with the probe (T99, electrical touch, type 0), run `eyes-carrier-v2_probe.ngc`, bring
`probe-results.ngc` back to the laptop.

**Carrier mill job opened (2026-09-26, evening).** `~/PCBMill/eyes-carrier-v2` created with `pcbmill new` from
`gerbers/` (B.Cu, ONE merged drill, Edge_Cuts, .kicad_pcb). `drill-info`: 3 tools, 71 holes, span 4.27 × 2.46 in;
`consolidate`: T1/T2 0.0465 → 0.0465, T3 0.125 → 0.125, all error +0.0000, annulus ≥ 0.25 mm. Set
`cam.isolation_width 0.03` and `cam.outline_enabled true` (job defaults were None/False). **Blank: PATIKIL single-sided FR-4 150 × 100 × 0.8 mm, 5 pcs at SLN RB-06** (/web/part/1082/, bought
2026-08-23). I first reported "no blank in stock is big enough" — WRONG: the search found it and my `tail -40` cut it
off (see memory truncated-search-absence). Board 117.88 × 72.29 mm sits on it with ≥ 0.55 in spare per side;
MDF fixture is 6⅛ × 4⅛ in (Scott). Job: blank 5.906 × 3.937 × **0.0315 in** (0.8 mm — NOT the 0.062 default);
`solve-offsets` → x_offset −6.8906, y_offset 5.9405, copper extents X 0.632..5.274, Y 0.545..3.392 in, centre
error 6e-5. **0.8 mm stock changes the depths:** verify check 5 wants every hole bottom between −0.003 and
−0.030 in below the backer, and applymap runs absolute (bottom = copper height + zdrill), so the 0.062-in
defaults (zdrill −0.075, zcut_outline −0.08) would land 0.0435 in into the MDF and FAIL. Set `cam.zdrill −0.045`
(→ ≈ −0.0135) and `cam.zcut_outline −0.05` (profile ≈ 0.0185 into the backer, what deskv1 did). The probe map is
what the audit actually measures against, so re-check after `probe-import`. Still to do in the job, in order: set `blank.*` to the
real blank, `solve-offsets`, `probe-gen`, `deploy` — ALL DONE by 13:00 (see the paragraph above); next is Scott running the
probe on the machine, then `probe-import`, `touchoff`, `regen`, `verify`, `runsheet`, `deploy`.

**Carrier back chamfers 4 mm deeper (2026-09-26, later still).** **FITS** — second wood copy sits inside the green panel (Scott: "probably took off more than you needed to, but it simplified it, so I think it's fine"). Outline frozen for V2. Corner-to-corner still stuck out past the green
case panel at both back corners (Scott's third photo, red arrows). Scott: "has to come in like probably four
millimeters is my guess on either side … indented slightly from the green panel." OUTLINE: the corner-to-corner
line moved 4 mm inward, parallel — back-edge end -40.598 → -35.420, side end 18.361 → 12.061, mirrored about
x=0.016. **That number is his estimate, not a measurement of the panel**; two caliper readings per corner (where
the case chamfer starts along the back edge and where it ends along the side) would replace it. **No placement
moved** — placement.py is byte-identical. Two traces did, because the new edge cut through them: the +5V trunk
turned north at x=-37.9, and (-37.9, 34.5) is 0.5 mm outside the deeper chamfer (edge is at y≈34.0 there), so it
now turns at -33.8 → (-33.8, 18.2) → TP2; and the +12V vertical moved 50.5 → 47.5 because the chamfer meeting
the old x=50.5 run left the pour 0.1 mm to get from the right edge into the J1 pocket — it poured as two
islands (U2 pad 12 unconnected). First attempt moved TP5 instead (54, 7.5 → 54, -11); Scott objected, rightly:
the trace was the thing in the way, not his test point. TP5 back at (54, 7.5). DRC+parity 0/0/0, ERC 0, pour
one polygon, gerbers/fit-check/STEP regenerated. Drills unchanged.

**Carrier outline fixed from the wood fit check + silk enlarged (2026-09-26, later).** The wood copy against the
green case showed the back corners wrong: the DXF had a kink 13 mm in from each back corner (14.5 mm at 62° then
10.4 mm at 34°) where the case runs one straight chamfer, wood sitting up to 4.7 mm inside it. Scott: "I must have
messed up the DXF when I cleaned it up." Fix in `gen/gen_pcb.py` OUTLINE: the two kink vertices dropped, chamfer now
corner to corner (21 vertices). `outline.dxf` is therefore NOT the master any more — the OUTLINE list is; a
re-export from Fusion must be diffed against it, not pasted over it. Silk read small on the wood: `text()` default
(refdes) 1.0 → 1.2, pin labels 0.8 → 1.0, legend 0.9 → 1.2 (dated 2026-09-26); the LM2596 IN/OUT labels moved
1.3 mm inward to clear its outline (2 silk_overlap warnings otherwise). DRC+parity 0/0/0, ERC 0, pour one polygon,
gerbers + drill re-exported, fit-check SVG and STEP regenerated. Drills unchanged, so the pcbmill gate result stands.
Every carrier hole lined up in the wood (holes ≈ kerf big; H-holes took a 0.130 in gauge pin).

**Carrier legend onto the real board (2026-09-27).** `python3 hardware/fitcheck/make_fitcheck.py --board` → `hardware/fitcheck/eyes-carrier-silk.svg`: same drawing as the fit check, but outline + 71 holes are **blue = align only** (set to not output in XCS, line up on the milled holes with the camera), **black** = F.SilkS legend incl. `EYES CARRIER V2 2026-09-26`. Component (bare FR-4) face up, NOT mirrored. One script for both so the fit check and the legend can't drift. **No recorded laser setting for marking FR-4** — the Score 10 %/200 mm/s row is basswood; test on the blank offcut first and record the row in `~/code/docs/laser/README.md`.

**Carrier legend: bare FR-4 after all (2026-09-27, evening).** **Fiber** (not blue — Scott corrected) Score **85 %/300 mm/s / 30 kHz ×4** marks bare FR-4; the real board took that job TWICE (lighter laminate than the test piece) and survives an IPA wipe (75 % ×1 was soot only). No paint needed. Recorded in the sln-ha-config fab guide §7. **Still open:** calibrate the P2S distant-view camera (xTool 1752).

**Carrier legend: the laser file is a RASTER (2026-09-27).** `python3 hardware/fitcheck/make_legend_png.py` → `eyes-carrier-legend-1200dpi.png` (5569×3415 px = 117.88×72.28 mm, canvas = Edge.Cuts extents, pixel size asserted). The SVG stays as the camera guide only: KiCad stroke-font text imports into XCS hollow/doubled, and the shop's measured legend recipe (sln-ha-config fabrication guide §7 profile B: blue diode, bitmap, 100 µs, 1–75 %, 500 DPI, 1 pass; deskhack needed 2) is for **white Rust-Oleum flat over FR-4, 12 h cure** — bare FR-4 'reads far worse'. Register by giving the PNG the blue outline's X/Y/W/H (4.641 × 2.847 in). P2S camera is off (see ~/code/docs/laser/README.md); the F1 Ultra camera aligned this board cleanly.

**Carrier laser fit check (2026-09-26).** Scott lasers a copy of every board in 1.5 mm basswood (outline + holes)
before the mill runs. `python3 hardware/fitcheck/make_fitcheck.py` → `hardware/fitcheck/eyes-carrier-fitcheck.svg`
for xTool Creative Space: **red** = cut (closed outline path + all 71 holes as stroked circles at the nominal drill
diameter, 1.181 / 3.175), **black** = engrave (F.SilkS incl. the V2 legend). Top view, NOT mirrored. Reads the board
file only, so it runs with KiCad open. Rejected handing over kicad-cli's own SVG: it draws drill marks as filled
discs (XCS would engrave them solid), outline in light grey and silk in pale yellow (no colour Scott can select on),
its viewBox has no stroke margin so the right/bottom edges clip, and it carries opacity-0 `<text>` helpers that XCS
imports as text objects. Regenerate after any placement/outline change; the holes are the drill sizes with no kerf
allowance, so a laser hole comes out a kerf larger than the milled one — fine for a fit check, not a gauge.

**Carrier: J1 placed by Scott, C1 turned, schematic parity clean (2026-09-26, later).** My J1 move left its body
against the buck's IN- corner; Scott put it at (45.05, 15.7) rot 180 between H4 and the chamfer and turned C1 180 to
(-39.75, 17.0) so the +5V stub from TP2 just continues west into C1.1 (the diagonal off the lane is gone, and with it
the C1 pour sliver: the pour is ONE polygon now). +12V: J1.1 east under J1 to x=50.5, north to TP1 (straight north
would graze IN- by 0.05). **The "schematic parity" errors Scott saw were the generator's, not the GUI's:** (a) NC
pads carried no net while the netlist names each one `unconnected-(REF-PIN-PadN)` (30 errors), (b) footprint
Description vs symbol "" (15), (c) Datasheet "" vs "~" (15), (d) J1 value "12V in" vs "12V pigtail". gen_pcb now
assigns the unconnected nets from D1_NAMES/PCA_NAMES, gen_sch copies each footprint's descr into the symbol and
writes Datasheet "" and "12V in". `kicad-cli pcb drc --schematic-parity` is now part of the check: 0/0/0, ERC 0.
`docs/animatronic-eyes-pcb.step` is re-exported with `kicad-cli pcb export step --subst-models` after every
regeneration (Scott exported one from the GUI; it went stale the moment the board was rebuilt).

**Carrier: J1 turned + moved, D1 model fixed (2026-09-26, Scott's review of the 3D view).** (1) J1 stood on the
right edge with its wire entry facing that edge - no way to get wires in. Now at (50.5, 14.5) rot 180, below the
buck, **wire entry toward the PCA edge = the back of the box (Scott)**; the wires leave over the chamfered corner.
TP5 moved from under it to (54.0, 7.5). +12V now runs J1.1 north along x=50.5 to TP1 with the y=2 run to IN+ teeing
off it; J1's GND pad got a solid pour connection (it is the whole 12 V return, like the buck IN-). DRC 0/0/0, pour
still one polygon + the 1.5 mm² C1 sliver, gerbers + drill re-exported, pcbmill bit map exact and annulus gate
passed. (2) ratgdo's D1 file is the module on female sockets; Scott solders the male headers straight in, so
`3dmodels/D1_Mini_ESP32_male.stp` is that file with the socket solid unlinked (one STEP line deleted, see
footprints.py) and dropped 8.5 mm; the 32 MB socketed original is gone from the tree (git history has it).

**Carrier 3D models attached (2026-09-26).** Every footprint carries a `(model ...)` block, emitted by
`gen/footprints.py` (`model()` helper, `models=[...]` per footprint), so the 3D viewer / STEP export show the real
stack. Sources: `hardware/carrier/3dmodels/` (34 MB, committed on purpose - the ratgdo files are not in any package
manager) holds `D1_Mini_ESP32.stp` + `LM2596.step` copied from Scott's ratgdo KiCad project with ratgdo's offsets
(same pad frames), and `PCA9685.step` from `~/Downloads/16-channel-i2c-servo-controller-1/` (GrabCAD-style, 'antoi'
2022 - the same file Fusion's Electronic Parts library uses; the Fusion MCP timed out on the export and then reported
"unavailable" for the rest of the session, so the Downloads copy was used). Terminal block, caps, resistor and test
points are stock KiCad 10 models; KF301 uses the Phoenix MKDS 1,5 model rotated 180 + 5.08 offset so the wire
entry faces the board edge. **PCA9685 transform is rotate (-90,0,180), offset (-0.18,-0.36,2.54), found by
rendering candidates, not by reading the STEP** - see TRAPS. Verified by `kicad-cli pcb render` top-ortho crops
(module holes centred on H3/H4, header pins on the U2 pads) and a right-side view. Model z = 2.54 (header plastic);
the real height is whatever standoff goes at H3/H4 - Scott's call, and the D1/LM2596 heights are ratgdo's guess of
header plastic too. Renders in `out/` (gitignored): `render_iso.png`, `render_right.png`, `render_top_hi.png`.

**Carrier V2 ROUTED + EXPORTED (2026-09-25, late), not cut.** Workflow now: Scott places in the KiCad GUI → (KiCad
closed) `python3 gen/capture_placement.py` copies positions into `gen/placement.py` → `python3 gen/gen_pcb.py .` rebuilds
the board around them (outline from the DXF, hole keepouts, D1 antenna/flash keepouts that follow U1, pour, legend).
Why: the GUI-only path broke the outline once already (23 loose Edge.Cuts lines; a box-select drag moved the ones inside
the box and J1/C1/TP5 were then placed 25 mm off the real board). State: ERC 0, DRC 0 violations / 0 unconnected / 0
footprint errors; `export_for_mill.sh` run (gerbers/, ONE merged drill: 3 tools, 71 holes, all exact bit sizes, annulus
gate passed in a throwaway pcbmill job); copper view `out/bcu_small.png`. **Routing (all in `TRACKS` in gen_pcb.py, the
docstring there is the map):** +12V J1→TP1 and along y=2 under the buck to IN+; +5V OUT+ → lane between slot and buck →
over H4 → lane outside the PCA right row → bar along the front edge (y 34.5) → up the left wing at x −37.9 → TP2 →
y 10.9 under the D1's outer row → x −53 (USB end) → y −2 through the module middle → VCC pad 35; C1/C2 hang off that
run (C1 from the lane by a diagonal, C2 from the y 10.9 run). +3V3 pad 16 → module middle y −12 → USB end x −52.5 →
y −23.5 behind the D1 → lane x −17.2 beside the slot (0.75 mm past the module's antenna-end PCB edge — the one
compromise; DC only) → PCA left-row VCC from inside. I2C pads 24/26 → east along y 9.3/10.5 → lanes x −23.6/−24.8
east of H3 → PCA left row pads 3/4 from inside. The right row carries only +5V/GND; the jumper groups cover the rest.
GND pour is ONE polygon (checked by counting `filled_polygon`s) plus a 2 mm² sliver hanging on C1.2's south spoke. Placement (board frame, y down): D1 Mini left wing
rot 270, USB-C overhanging the LEFT edge, antenna end at the slot; PCA along the BOTTOM edge, servo headers facing
the bottom edge, **centred on H3/H4 — its own holes line up with the carrier's (Scott)**, so it bolts down there and its
GND pins 6/12 sit 2.25 mm from the hole centres (the module's own geometry: nylon standoff/washer at H3/H4, and those two
pads plus the buck's IN−/OUT− get SOLID pour connections — servo return current, and the keepout leaves them one spoke);
LM2596 right wing, OUT at the top edge, IN at the bottom; **12 V comes in on the U3 (right) side about mid-depth
(Scott):** J1 sits against the right edge at y ≈ 2–7 with its wire-entry face toward the edge, TP1 above it, TP5 below.
The 12 V source is a **panel-mount 5.5 × 2.1 DC jack** (M8 × 0.75 thread, ⌀10 face, solder lugs 5.2 mm apart, 2.5 × 0.8
lugs): it lives in the rack panel, two wires to J1 — center pin is +12V by convention, check the wall wart is
center-positive. C1/C2 + TP2 below the D1 in the left wing. `min_resolved_spokes` is 1 in the .kicad_pro:
the D1's third GND pin (33, inner) can only get one spoke and the other two carry the return.
V1 history: `hardware/carrier/`: KiCad 10 project generated by `gen/footprints.py`
→ `gen/gen_sch.py` → `gen/gen_pcb.py` (run in that order; the PCB reads symbol uuids from the schematic). Generated
rather than drawn in the GUI so every coordinate is in one reviewable file and the whole board rebuilds from the DXF;
open it in KiCad freely, but if you move things there, the generator becomes stale — say which is the master. ERC 0,
DRC 0 errors / 0 warnings / 0 unconnected; `export_for_mill.sh` writes gerbers + ONE merged drill + legend/mask SVGs, and
a throwaway `pcbmill consolidate` mapped all three drills to owned bits with zero error and passed the 0.25 annulus gate.
Renders in `out/` (regenerate with `kicad-cli pcb render`). Decisions, and what was rejected:
- **PCA9685 geometry is Adafruit's rev C Eagle board** (github adafruit/Adafruit-16-Channel-PWM-Servo-Driver-PCB, master
  branch — `main` 404s): body 62.23 × 25.4, two 1×06 rows 58.42 apart, pins V+/VCC/SDA/SCL/OE/GND from the servo edge.
  Its holes are 55.88 × 19.05 — NOT the carrier's 57.0 — so **the PCA has no mounting holes on the carrier; it sits on
  its two soldered headers** (M2.5 standoffs would hit the header plastic anyway). Clone assumed identical: **calipers
  before cutting** (row spacing, pitch), same for the LM2596 pin grid (17.6 × 39.8, ratgdo's numbers).
- **Placement V1 REJECTED by Scott (2026-09-25).** I put the PCA across the slot with the D1 Mini in the bottom band.
  The servo wires enter from the BACK of the rack — the side where the D1 Mini was — and the slot is a clearance area a
  servo passes through, so a PCA lying across it blocks that servo. I had never asked which edge the servo wires come
  from. **Scott is doing the layout himself in the KiCad GUI**; the schematic, netlist and footprints stay as generated.
  Superseded the same evening by the capture → regenerate workflow above (placement.py is the master for positions,
  the generator for everything else). The pin choices below were forced by the rejected placement and are OPEN again:
  in Scott's placement the D1's outer-bottom row (pads 22/24/26/…, y ≈ 7.5) faces open board toward the PCA and the
  inner rows exit through the module middle — recheck which of 21/22/34 vs 25/27 route before touching firmware.
- **I2C pins, decided by V2 routing: SDA = IO27 (pad 24), SCL = IO25 (pad 26). Firmware for the carrier build:
  `Wire.begin(27, 25)` — NOT changed yet; the DevKit build keeps 21/22.** IO21/IO22 (pads 27/25) are INNER-row pins in
  Scott's placement: the inner row can only leave through the module middle and out its USB or antenna end, and the USB
  end already carries +5V and +3V3 — reaching 21/22 meant a track under the antenna or through the flash-pin block, so
  rejected. Which of 24/26 is SDA is forced too: 24 is the eastern pad, so it takes the outer lane round H3 and lands on
  the lower PCA pad (SDA, pad 3); swapping them crosses. IO34/IO36 are moot (divider gone).
- **Rail monitor DROPPED from the carrier (Scott, 2026-09-25).** R1/R2 10k/10k divider, the RAIL_ADC net and TP4 were my
  assumption, not his plan. Evidence (rail-monitor section above): the ADC's sag counts are its own noise and the real
  sag was only visible on the scope, so on a board with the buck set to 5.0–5.1 V the reading buys nothing a meter on
  TP2 doesn't. Removed from `gen/gen_sch.py` and regenerated (TP numbers kept: TP1/2/3/5/6). Firmware unchanged: Rail.cpp reports "not wired" when the pin floats. IO36 is free again.
  Test points that remain: TP1 +12V, TP2 +5V, TP3 +3V3, TP5 GND, TP6 GND.
- **+5V is a daisy chain, not a star, in V2:** OUT+ → PCA V+ (right row) → front-edge bar → left wing → D1 VCC. A
  separate run to pad 35 would have to cross the +3V3 lane or the GND paths into the left wing. `jumper_pad_groups` on
  the PCA footprint (KiCad 10 accepts it) is what lets the right row carry +5V/GND only and the left row everything
  else without DRC "unconnected". Rejected alternatives that DRC would have passed but the copper would not: I2C to the
  right row across the front bar (crosses +3V3); +3V3 down the far-left edge (fills the 1.35 mm strip that is GND's only
  way into the D1's middle); feeding C1 by a stub from the y 10.9 run (walls off a pocket around C1's GND pad — the pour
  then hangs on that pad's spoke alone; KiCad keeps it because a pad counts as a connection).
- **Compromises:** C1/C2 are ~35 and ~25 mm of trace from pad 35 (round the USB end), not "a few mm" — an inner pin on
  a single-sided board with the module on headers cannot have parts beside it. No SDA/SCL test points: probe U2's left
  header pins 3/4 on the copper side. The GND strip under the +5V bar is 0.94 mm and the one under PCA pad 1 is 0.89 —
  both above the 0.5 min width, both real paths (the left wing also has the far-left strip).
- **D1 Mini pad numbering is r0oland's (the ratgdo library).** espboards.dev's table disagrees; **photograph both rows
  of the actual module's silk before cutting** and check pads 4, 16, 24, 26, 33, 35 against it.
**Still to decide (Scott):** which face points at the rack and the height available (buck module ~10
mm, PCA headers + servo plugs); calipers on the clone PCA and an LM2596; D1 Mini from BO-0009 or bought; KF301 (#291)
onto BO-0010's BOM and the passives allocated once the design is frozen.
**Firmware for the swap:** PS4Controller applies a host MAC via esp_base_mac_addr_set (BT − 2, IDF's own rule), but
the sketch starts Wi-Fi before PS4.begin, so done that way only BT would take the DevKit's identity. Setting the
base MAC at the top of setup() makes Wi-Fi inherit it too, so the 192.168.30.211 reservation carries over.

**Carrier probe map imported, RED-FLAGGED (2026-09-26, ~14:50).** Scott ran the probe and dropped
`~/Downloads/probe-results-eyes.ngc` (160 points, full 16 × 10 grid); `probe-import` took it into
`probe/probe-results.ngc`. Numbers: span **0.021 in** (min −0.0196 at the lower-left corner X0.05 Y0.05, max +0.0014
at X4.23 Y1.73), plane tilt 0.0022 in/in in X, roughness RMS 0.0007 (limit 0.0005), worst point X4.99 Y0.05 at
−0.0022 off its neighbours (limit 0.0015). Shape: a smooth dome — the ridge runs up the board at X ≈ 4.2 and the
whole left edge sits 16–20 thou low; the bottom row (Y 0.05, the by-eye edge) is 2–4 thou below the row above it
across the middle columns. Excluding the top and bottom rows the interior roughness is 0.0005 RMS, worst +0.0014.
For scale, the four deskv1 maps (Downloads, Aug 13) spanned **8–12 thou** with interior roughness 0.0001–0.0002 —
this blank is 2× the span and 3–5× the roughness of anything cut so far. Inside the board footprint (X 0.63..5.27,
Y 0.55..3.39) the span is still ~15 thou. Reading: NOT voids (no isolated bumps) but the blank is not seated — bowed
up on a thick wax film under the right-center, or a lump under it. pcbmill's gate says do not cut; `touchoff`,
`regen`, `verify` are not blocked by the flag, only advised against. Scott to check the seat physically (press the
ridge at ~4.2 in from the left, 2 in up; a board that moves or clicks is lifted). Re-mount and re-probe, or accept
the dome and cut with applymap following it — Scott's call.

**Carrier CLEARED TO CUT (2026-09-26, ~15:00).** Scott pressed the ridge: "board is solid, accept the dome and cut."
`touchoff`: jog to **X4.2300 Y1.7300**, V-bit electrical touch, type **0.0014** into TOUCH Z; validate at X0.05 Y0.05
(DRO −0.0196) and X3.09 Y2.15 (DRO −0.0031). First `verify` FAILED check 9 (slivers): at isolation 0.030 the
2.54 mm-pitch U1/U2 header rows leave 16 copper slivers 0.29–0.93 mm wide between pads, each needing ≥ 0.036–0.039 in.
Set **`cam.isolation_width 0.04`** (pcbmill's own suggestion; deskv1 ran 0.03 but had no header rows this tight),
regen, verify → **JOB READY**, 12 checks, 9 and 10 WARN only (14 slivers left: 7 planned pour-exclusion islands,
7 WARN-grade). Rejected re-drawing the pads oval in KiCad: right fix for v3, but it re-opens the design for a board
already mounted. Run sheet at `~/PCBMill/eyes-carrier-v2/out/runsheet.txt`; deployed to `/Volumes/Tormach/gcode/`:
`eyes-carrier-v2_back_comp.ngc`, `_drill_comp.ngc`, `_outline_comp.ngc` (+ the probe program, unchanged content).

**Carrier: isolation program REDEPLOYED without G37 (2026-09-26, ~15:30).** Scott, reading the run sheet: "are you
having it check tool length on all but 600?" It was checking all of them, T600 included — issue 002 (Aug 13) had put
G37 on every tool, contradicting the sheet's own "ELECTRICAL touch-off MANDATORY" line for the V-bit (ETS +4.1 thou
vs work frame, 2 thou cut). Fixed in pcbmill (issue 004): back program is `G43 H600` only after the M0; drills and
the T610 outline keep G37; verify check 4 now FAILS a G37 on the isolation tool. Regenerated, JOB READY, all four
files overwritten on `/Volumes/Tormach/gcode/`. The 15:00 back_comp on the share was never run. Procedure at the
machine is unchanged: V-bit in, electrical touch at X4.23 Y1.73, type 0.0014 into TOUCH Z, run back_comp.

**ETS bias measured again on the carrier (2026-09-26, ~15:45).** Scott G37'd T600, drove to the touch-off node X4.23
Y1.73 and the electrical touch read **Z 0.0053** where the map says 0.0014: **3.9 thou**, against the 4.1 thou
pcbmill carries as `ets_frame_offset_in`. Second independent measurement of the bias. Answer given: enter 0.0014
via **Offsets tab → Touch Z** (sets the T600 tool length, G54 untouched), NOT the DRO Z window (moves G54 and drags
the ETS-measured drills and outline with it). Validation nodes: X0.05 Y0.05 → −0.0196, X3.09 Y2.15 → −0.0031.
Validation after Touch Z: X0.05 Y0.05 read **−0.0190** (map −0.0196, +0.6 thou), X3.09 Y2.15 read **−0.0038** (map
−0.0031, −0.7 thou). Map transfers to the V-bit frame within a thou; cleared to run back_comp.
**Isolation cut DONE (2026-09-26, ~17:30)** on the dome, with the G43-only program. Drilling next: T605 #56 then
T606 1/8, G37 in-program; then outline T610.
**Drilling DONE (2026-09-26, ~17:45).** Outline next: T610, G37 in-program, zcut −0.05.

**Outline moved to the T615 fishtail, ramped; keepout clearing on T610 (2026-09-26, ~20:40).** Scott: "last time we
used a ramping strategy on the outline", then "this should be a flat 1/8" but the outline should be the fishtail
cutter 615". Job now `tools.outline_t_number 615`, `cam.outline_tool_diameter 0.0945` (PreciseBits RCC08-0945-039F,
deskv1's profile tool); isolation and drill programs regenerated byte-identical. pcb2gcode can only plunge
(F5, one full-depth lap), so `manual/make_ramped_outline.py` in the job dir rebuilds the outline from the
pcb2gcode path: CCW (climb with M3), **3 passes at −0.0167/−0.0333/−0.0500 below LOCAL copper** (probe map, same
as deskv1's ramp shape but height-compensated), 1 in ramp entry at F10 then the lap at F15, G37 H615 in-program.
XY extents X 0.585..5.321 Y 0.498..3.439, lowest Z −0.0641, 0.0185 into the MDF everywhere. Deployed as
`eyes-carrier-v2_outline_ramp.ngc`; the plunge version `eyes-carrier-v2_outline_comp.ngc` (also T615 now) stays
on the share but is NOT the one to run.
Keepouts: `pcbmill regions` lists 7 B.Cu rule areas, all pour-exclusion only. Four (1,3,4,7 — the 6.5 mm
standoff keepouts) hold H1–H4 and are NOT rastered (the island is the mounting-hole annulus). Three are empty and
now cleared: **area 6** (X 3.66..3.98 Y 1.64..2.88, the antenna keepout beside U1, 19 raster passes), **area 2**
(X 4.73..4.93 Y 1.66..1.86) and **area 5** (X 4.73..4.93 Y 2.66..2.86), the flash keepouts. Generated with
`pcbmill clear N --tool 0.125 --depth -0.005 --tool-number 610` (deskv1 precedent), height-compensated, G37 H610
in-program. `pcbmill clear` had REFUSED all seven as "not a full copper keepout" because the rule demanded
tracks/vias/pads not_allowed too — a KiCad pour-exclusion is exactly the island the cycle exists for, so pcbmill
now refuses only regions holding copper or regions that admit the pour (tests in `tests/test_clear_policy.py`).
**Run order:** `clear_area6_comp.ngc`, `clear_area2_comp.ngc`, `clear_area5_comp.ngc` (T610, one tool change
for all three), then `eyes-carrier-v2_outline_ramp.ngc` (T615). `--tool-number 610` is mandatory now that the
job's outline tool is 615: without it clear would emit T615.
**Clearing merged into ONE file (2026-09-26, ~20:50).** Scott: "why isnt the clearing in 1 file?" No reason but
pcbmill's `clear` being one region per call. `out/eyes-carrier-v2_clear_comp.ngc` = the three `_comp` bodies
(6, 2, 5) under one header and one T610 tool block; each section starts at clearance Z 0.0929 before its XY
rapid. Deployed; the three single-area files were removed from the share (still in `out/`). **Run order now:**
`eyes-carrier-v2_clear_comp.ngc` (T610), then `eyes-carrier-v2_outline_ramp.ngc` (T615).
**Assembly BOM check (2026-09-28, Scott assembling today):** InvenTree part #837's BOM (BO-0010) still lists
**2× 10k 1/4 W for the rail divider, which the carrier dropped** — REMOVED 2026-09-28 at Scott's OK (BOM line 142).
The BOM also has no line for the 12 V adapter, the M3 standoffs or the D1 Mini headers. Carrier schematic
(kicad-cli BOM): C1 220u, C2 100n, J1 KF301, U1 D1 Mini, U2 PCA9685, U3 LM2596, TP1/2/3/5/6, H1–H4. Still open
at assembly: D1 Minis both allocated to BO-0009; stock 683 adapter is shrink-fit's; firmware still on the
default I2C pins (carrier needs `Wire.begin(27, 25)`).
**Carrier STUFFED (Scott, 2026-09-28).** Not yet powered. Bring-up not done: whether the LM2596 was set to 5.0 V
before it was soldered in is not recorded (its OUT+ is hard-wired to C1 [10 V], PCA V+ and D1 VCC, so an unset pot can
put ~11 V on all three). Firmware still calls `pwm.begin()` on the default Wire pins (21/22): the carrier needs
`Wire.begin(27, 25)` before it or the PCA will not answer.
**First power (Scott, 2026-09-28): 3V3 pin reads 2.7 V.** Everything else "looks good" (Scott). Not on Wi-Fi at
.211 at the time (/status gave nothing). Cause NOT established. Discriminator asked for: TP2 (+5V) at the same
moment. TP2 ~5 V → 3V3 is being loaded (bridge on the milled +3V3 lane, or the regulator is overloaded/boot-looping;
check TP3–TP5 ohms powered off, and feel the D1's regulator). TP2 low → the supply side (buck set low, or USB-only
power through the D1's diode). I2C firmware change (27/25) committed and compiled, not flashed.
**TP2 = 5.08 V (Scott, same power-up).** Supply side ruled out: 3V3 is being loaded or the D1's regulator is failing.
Pad maps re-read (footprints.py D1_NAMES 16=3V3/35=VCC, PCA_NAMES V+,VCC,SDA,SCL,OE,GND): consistent, not verified against the module.
**TP3–TP5 powered off = 2 MΩ (Scott).** No static short on +3V3. Left: the D1 not actually getting 5 V at its own
VCC/GND pins (joint or trace between TP2 and pad 35, or its GND pads), a weak regulator, or a boot-loop load (read the USB boot log).
**Thermal photo, powered (Scott):** ambient 74.0 °F, ESP32 module can 91.2 °F (the hot spot), the part at the D1's top
edge 76.7 °F (read as the regulator — which part it is is my guess from the image). No hot spot: rules out a heavy
load and an overloaded regulator; an ESP32 running at ~+17 °F is normal. Module-pin 5V/3V3 readings still not taken.
**D1 flashed on the carrier (2026-09-28), build 30e6860 over USB.** The chip read as ESP32-D0WD-V3 rev 3.1, 4 MB, flash
3.3 V strap. What was on it before printed a repeating garbage line at 115200: foreign firmware, not ours. Boot log
after the flash: base MAC d4:8a:fc:9e:7a:cc adopted (BT …:ce), Bluetooth up, **PCA9685 prescale 254 (answering) on
IO27/IO25**, Wi-Fi at 192.168.30.211 rssi −36. DevKit unplugged (Scott). **Settings are defaults:** 22 of 43 keys
differ from docs/settings/2026-09-25-devkit-values.json (trims, centers, lid presets). Controller not tried yet; no
NVS copy was made, so this is the "MAC alone" path.
**The 2.7 V was read while the foreign firmware ran.** Not re-measured on ours yet. **Thermal on USB power (Scott):**
a 115 °F spot at the D1's USB corner (ambient 74.4); on 12 V that corner was ~77 °F. So the hot part is on the USB
path — on USB the D1 feeds the carrier's whole +5V net (PCA V+, the buck's output). Which part it is: not identified.
**3V3 still 2.7 V on our firmware (Scott, USB power), with Wi-Fi, BT and the PCA all working.** Which point he probed
(TP3 or the D1's pin) is not recorded. Next discriminator: the D1's own 3V3 pin to its own GND pin, then TP3 at the
same moment. Equal → the module's regulator/rail is low. Pin 3.3, TP3 2.7 → an open or high-resistance joint in the
milled +3V3 path (pad 16 → under the module → lane x −17.2 → PCA VCC).
**Scott suspects the D1 pinout (2026-09-28).** Evidence so far, D1 side: the footprint's own map came from ratgdo (their
board: 16 = +3.3V, 35 = +5V, 1/22/33 = GND), so that is not an independent check. The FUNCTION is: the ESP runs on 12 V
through the buck (pad 35 + GND right) and the PCA answers on Wire.begin(27, 25) (pads 24/26 right; a mirrored or shifted
footprint would put those on other pins). Pad 16 sits in the same footprint, so a wrong D1 map is unlikely but not
ruled out: the Type-C "D1 Mini ESP32" clones are not all the MH-ET LIVE pinout. Decisive and cheap: read the module's
own silkscreen at the pin the TP3 trace reaches.
**3V3 is 3.3 V at the D1's pins (Scott, top side, USB power): 3V3 pin 3.3, 5V pin 5.2.** Scott withdrew the pinout
suspicion. From the copper side the "same" pins read −1.9 V (3V3) and 0 V (5V). −1.9 = 3.3 − 5.2 exactly, and 0 = 5V
against itself: the fit is that the black lead sat on the 5V pin when probing from underneath (mirrored view), not a
fault — a header pin is one piece of metal top to bottom. Hypothesis until re-probed underneath against TP5. The
earlier 2.7 V is then also suspect as a probe-reference reading, not a rail fault. Open: that re-probe.
**Correction (Scott): the black lead WAS on ground both times, not between the pins.** So the question is which copper
he used as ground underneath: the −1.9/0 pair is what a reference on the +5V net reads. Check that spot to TP5.
**Measured on the D1's regulator itself (Scott):** carrier-powered (12 V → buck), one pin 5 V and the output 2.7 V; on USB
the 3V3 pin reads 3.3. Reference was ground (Scott) — which ground point, TP5 or the regulator's own GND pin, not
recorded. Open split: output vs the REGULATOR's GND pin (3.3 → the regulator is fine and the D1's ground sits ~0.6 V off
the carrier's, i.e. its GND pins/pour spokes; 2.7 → the regulator), plus the regulator GND pin vs TP5.
**Likely cause found (Scott): a D1 GND pin was never soldered.** The pad has thermal-relief spokes to the pour and
is small, so it did not read as needing a joint. Fits the ground-offset reading (regulator 3.3 V over its own ground,
2.7 V against the carrier's; fine on USB, where the cable grounds the D1). **CONFIRMED 2026-09-28: soldered, 3V3 = 3.3 V against TP5
on carrier power (Scott).** The carrier's power is done. Design note for a V3: give the D1 GND pads solid pour connections like
the PCA's pins 6/12, and mark them in the legend.
**Settings restored on the D1 (2026-09-28, Scott's pick: the 09-25 snapshot, not a fresh DevKit read).** 22 differing
keys POSTed to /set, then /save; /values read back matches the snapshot on all 42 keys, dirty false. Not re-read after a
power cycle. Anything tuned on the DevKit after 09-25 is not on the D1 (the DevKit still holds it, unplugged).
**Thermal after the GND fix (Scott, 2026-09-28):** ambient 75.0 °F, ESP32 can 89.2 °F, hot spot 107.6 °F (42 °C) at the
D1's USB-end corner, where the two small parts sit (which one is the regulator: not identified). Power source for this
shot not stated. Before the fix that corner was ~77 °F on carrier power and 115 °F on USB. 42 °C is an ordinary LDO
temperature at ESP32 load (5 → 3.3 V); no action.
**Controller CONNECTED to the D1 (2026-09-28): the "MAC alone" path works** — base MAC adopted, no NVS copy, no
re-pair. /status: conn true, mode live, pca true, pcaPrescale 101 (= 25 MHz / (4096 × 60) − 1, correct). The first boot on
the carrier logged prescale 254, read while the D1 GND pin was still unsoldered; after the fix and a power cycle it
reads 101. Link between the two not tested. **Swap checklist complete:** flashed, .211 kept, settings restored,
controller paired. The DevKit stays unplugged (same MAC).
**After moving the servos (2026-09-28): "can't reconnect the controller" (Scott).** /status right after his message:
conn TRUE, mode sleep (lids 60, x/y 512) — so it HAD reconnected after the power-up and then gone to sleep on the
hands-off timer (handsOffSecs 30). Seconds later conn false, still sleep. Cause of the drop not established.
**Reconnect timed (14:23, /status every 2 s):** P4 → conn true at 14:23:36, false again at ~14:23:57 (~21 s), mode stayed
sleep throughout (no takeover registered), no ESP reset. Connect-then-drop, repeatable. Candidates, none tested: the D1
has no link key for this controller (NVS not copied; the first connection may have been a fresh auth that wasn't
stored), or no input packets arriving. Next: serial log (PS4 connected/disconnected + stat pkts/s) during a P4 press,
read with DTR/RTS held low so opening the port doesn't reset the board.
**Controller battery readout added (build 6314000, OTA 2026-09-28 ~14:26):** /status `batt` (DS4 0..10, 11 = full while
charging; −1 = no packet since boot) and `charging`, on the page's status line, and in the serial disconnect line. The
value is the LAST reported, kept after a drop. Scott suspected the ~21 s drops were a dying controller battery (light
wouldn't stay lit). **My OTA restart dropped a connection Scott had just made on USB charge power** — then "connected but
no control": /status said conn false from the restart on. Don't flash while Scott is testing the controller.
Board side meanwhile fine: idle show ran on its own (x/y moving), pca true.
**Connected, no eye motion (Scott, 14:30, on USB charge power — so the DS4 DOES work over BT while charging).** Log:
14:30:11 conn true, batt 9, charging; 14:30:15 mode live (stick takeover received); 14:30:29 rest. So packets and stick
input reach the board: the fault is board → servos. **pcaResets = 1** since the 14:26 restart: the PCA lost its prescale
once and was set up again (its logic power or I2C blinked). Correction: my "eyes fine, idle show running" at 14:27 was
the board's commanded x/y, not seen motion. Next: did anything move since the servo move; V+ at a servo header; a
page-driven "lookL" while Scott watches.
**lookL test (14:3x):** POST /scene cmd=lookL → x 1023, pca true, prescale 101, nothing moved (Scott). Nothing has moved
since the servo move, not even at power-up. Plugs are in the same positions/orientation as on the old board. V+ at a
servo header 5.07 V — reference not stated, probably carrier ground. Firmware output path read (setPWM ch 0–5, full-off
only when limp): unchanged from the DevKit build except the Wire pins. **Leading hypothesis, untested: the PCA module's
own GND is not reaching the carrier** (same failure as the D1 pin): the servo GND row would float (servos can't move),
the chip could still limp along on I2C through its pin diodes, which would also explain pcaResets 1. Check: V+ to the
GND pin of the SAME servo header, and PCA GND pin ↔ TP5 continuity powered off. Then a scope on a signal pin.
**PCA ground hypothesis FALSIFIED (Scott):** V+ to the same servo header's GND = 5 V. Servo power and ground are fine.
Remaining: no pulses leaving the PCA. Next: DC meter on a channel-0 signal pin to GND (pulsing at 60 Hz × ~1.5 ms ≈ 0.3 V
average; 0 V = nothing out), then OE: it is unconnected on the carrier (by design) and whether this PCA module pulls it
low on its own board is not verified; OE-high disables every output while I2C still works. Test: jumper OE to the
adjacent GND pin on the PCA header.
**Scope, first look at the ch-0 signal pin (DHO914):** 200 mV/div, 500 ns/div, Normal trigger rising at 7 mV → flat 0 V
with ±0.2–0.4 V noise bursts; the trigger fired on noise. Inconclusive at that setting (a 16.7 ms period can't show at
500 ns/div). Re-taking at 1 V/div, 5 ms/div, trigger 1.5 V, Auto.
**Scope, proper setup (5 ms/div, 1 V/div, trigger 1.5 V, sweep Auto): ch-0 signal pin has NO pulses** — flat, ~200 mV
noise only (Scott). The PCA is configured (prescale 101 read back) and being written, yet emits nothing. Next: OE pin
voltage, then OE bridged to GND.
**OE = 0.25 V (Scott): low, outputs enabled — not the cause.** And the scope capture was INVALID: the board was in
mode sleep with sleepQuiet 1, which sets every channel full-off on purpose (no pulses by design). My miss — I didn't
check the mode before asking for the scope. Sent lookL (mode rest, pulses on) for a re-take. Board had been
power-cycled again (reset power-on, pcaResets back to 0).
**Scope re-take in REST (lookL/lookR sweep 15:01:02–15:01:34, then resting at x 1023):** 5 ms/div, CH1 200 mV/div with
−1.19 V offset (window ≈ 0.59–1.99 V), trigger 900 mV sweep Auto: NO trace in the window at all. 3.3 V pulses would cross
it on every edge, so no pulses — but where the trace actually sits (0, 3.3, 5 V) is off-screen, so which pin the probe is
on is not confirmed. Next: 1 V/div, offset zeroed.
**Scope at 1 V/div, offset 0, 5 ms/div, board in REST at x 1023 (Scott, ~15:05): ch-0 signal pin FLAT AT 0 V**, noise
spikes only. Rest is not limp (limp = quiet sleep only, Scenes.cpp:486), so channel 0 should be pulsing ~1.8 ms at 60 Hz.
Nothing moved on any of the six channels since the servo move, so the fault is chip-wide, not one pin: I2C works and the
prescale reads 101, which rules out bus and power, NOT the output stage. Chip-wide causes that leave the prescale intact
(hypotheses): MODE1 SLEEP set (oscillator stopped), EXTCLK latched with no clock, ALL_LED full-off, or OE high enough
(0.25 V is below the 0.99 V threshold, so unlikely). Instrument: GET /pca register readback (build below).
**PCA registers read back (build 030657e, GET /pca, 2026-09-28 ~15:15, mode rest):** MODE1 0x20 (auto-increment only:
SLEEP clear, EXTCLK clear, oscillator running), MODE2 0x04 (totem-pole outputs, normal), prescale 101, ALL_LED all 0,
channels 0–5 ON 0 / OFF 309, 387, 304, 375, 346, 330 counts (1.26–1.58 ms at 60 Hz). **The chip is configured, awake and
loaded with valid pulses, so I2C works end to end** (the D1's writes come back exactly) and every chip-wide software cause
is ruled out. The fault is between the chip's output stage and the header's signal pins: OE at the CHIP (pin 23; 0.25 V
was read at the header), the chip itself, the module's series resistors, or the probe row. Scoping SCL/SDA (Scott asked)
adds nothing now: a readback of what was written is stronger evidence than bus edges.
**Probe row confirmed (Scott, ~15:20):** servo plug off, tip on the labeled PWM pin (the colored row, V+ next, GND outside):
the pin sits at ~0 V; lifting the tip off drops the trace ~0.25 V below that. So the output is DRIVEN LOW, not floating.
With MODE2 OUTNE = 00 (read 0x04), the PCA9685 drives every output LOW when OE is high: exactly this. **Leading
hypothesis, untested: OE floats high at the chip.** On the carrier OE (U2 pad 5) is unconnected by design; the DevKit's
**6-wire** jumper most likely carried OE to a low, and this module may have no pulldown of its own. The 0.25 V "OE" meter
reading is also the same size as the probe's own offset, so it does not prove OE is held low. Test: jumper OE to the
adjacent GND pin on the PCA header. V3: tie U2 pad 5 to GND on the carrier.
