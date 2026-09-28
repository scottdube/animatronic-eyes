# Handoff: dead PCA9685 module forensics (written 2026-09-28)

Goal: find out whether the dead module's fault is the **chip** or a **solder joint / series
resistor**. Then salvage its parts (1000 µF cap, 221 = 220 Ω arrays, 103 = 10 kΩ pull-ups).
Scott has looked at the joints under the microscope and they look OK.

## What is established (full record: CLAUDE.md, 2026-09-28 sections)
- The module drove the carrier: all 6 channels read **0 V** (driven LOW, not floating) with full-on
  held (ON_H 0x10 on ch 0–5), OE jumpered to GND, and MODE1 0x20 / MODE2 0x04 / prescale 101 read
  back correctly. So I2C writes and reads worked and the chip was awake, yet no output moved.
- Moved to the known-good DevKit host, it was still flat, and there it read **prescale 254** (0xFE,
  the register's own address). A reply like that suggests a chip that is answering badly. This is a
  hypothesis, not established.
- A replacement module on the same carrier works (pulses verified, prescale 101). The carrier and D1
  are fine.
- One 220 Ω array covers ch 0–3 and another ch 4–7. All six channels being dead points at the chip
  (or its supply/ground), not a resistor array. This is not tested.

## What changed since that could trip the next session
- **The DevKit is ERASED** and earmarked for Florida (stock 878). It is no longer a test host. Use
  the D1 on the carrier.
- **The web-page OTA (df3c16b) crashed the D1 twice.** Each time it came back on df69225 with
  settings intact. The controller was connected both times, with heap ~28 KB. The out-of-memory
  cause is a hypothesis and untested. Flash over the D1's USB (`./build.sh usb`), or try OTA with
  the controller OFF. Don't loop OTA.

## Step 0 (added 2026-09-28, later): unpowered ohms, see CLAUDE.md. Pinout below VERIFIED vs datasheet.

## Fallback plan if the ohms are ambiguous (Scott has not yet approved it)
1. Bridge the dead module's **A0** pad so it answers at **0x41**. Wire its VCC/GND/SDA/SCL in
   parallel with the carrier's PCA header, so the working module at 0x40 keeps running.
2. Firmware: add `?addr=` to `GET /pca` and `POST /pcatest` (currently hard-wired to 0x40), and
   flash it together with the new page, over USB.
3. `POST /pcatest?addr=0x41&out=high`, then read `/pca?addr=0x41`. Probe at the chip, TSSOP-28
   pinout (verified vs NXP datasheet Rev. 4): **pin 6 LED0**, 28 VDD, 14 VSS,
   23 OE, 25 EXTCLK, 26 SCL, 27 SDA.
   - Chip pin 6 high but the header is 0 → resistor or joint.
   - Chip pin 6 low with VDD/VSS good → the chip.
   - Also check the prescale readback at 0x41: 101 means it's writable, 254 means the chip is bad.
4. Before every probe, read `/pca` so a hands-off sleep doesn't void the test (this happened twice
   on 09-28).

## Standing rules
- A flash drops the PS4 controller. Reconnect by holding P4 ~10 s until the light goes out, then
  pressing P4.
- Never OTA while /values says dirty, and never `FORCE=1` without Scott.
- The repo is PRIVATE (flash backups hold the link key).
