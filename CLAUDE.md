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
**Rail baseline, divider wired (2026-09-25).** ESP32 on USB; which supply fed the servos in this run is NOT
confirmed (probably still the bench PSU). Measured on the ESP32 5 V pin:
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
