# animatronic-eyes

A build of Will Cogley's **Basic EyeMech** (Nilheim Mechatronics): two eyes,
each moving on X and Y, plus four eyelids. Six SG90 servos run from an Adafruit
PCA9685 driver on an ESP32, and a PS4 (DualShock 4) controller drives it over
Bluetooth.

## Credit and license

The mechanism, the printable parts and the original Arduino sketch are
**Will Cogley's** work, published as the
[Simple Eye Mechanism (Basic EyeMech)](https://willcogley.notion.site/Simple-Eye-Mechanism-983e6cad7059410d9cb958e8c1c5b700)
under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
His original license notice is kept in `reference/License.html` and
`hardware/kit-stl/License.html`. For commercial use of his design, contact him
as that notice says. This repository cannot grant it.

Everything here is an adaptation of that kit or is built to go with it, so the
**whole repository is released under the same license, CC BY-NC-SA 4.0** (full
text in `LICENSE`). You may share and adapt it with attribution, for
non-commercial purposes only, and must release your changes under the same
license.

## What is his, and what changed

| Path | What it is | Relation to the kit |
|---|---|---|
| `hardware/kit-stl/` | The 15 printable STLs, `Complete Model.stl` and the license | **His files, unmodified** (kit downloaded May 2024) |
| `firmware/Low_Tier_Code/` | The kit's Arduino sketch | **His code**, plus three debug `Serial.println` lines |
| `reference/` | Kit images and license | **His**, unmodified |
| `hardware/kit-f3d/` | The 15 STLs converted to Fusion designs (faceted), plus the conversion script | Format conversion of his parts |
| `hardware/native/` | Every kit part rebuilt as parametric Fusion features, within 0.002 mm of his STL, plus SG90 models and an assembly | Adaptation of his parts |
| `firmware/Low_Tier_Code_mod_ps4/` | First PS4-controller version of his sketch (2024) | Adaptation of his code |
| `firmware/EyeMech_PS4/` | Current firmware: PS4 control, a web settings page with live sliders, Wi-Fi OTA updates and autonomous "scenes". His servo math is kept unchanged. | Adaptation of his code |
| `firmware/pca_bench_test/` | Bench test for the PCA9685 board | New |
| `hardware/carrier/`, `hardware/fitcheck/` | KiCad carrier board for the ESP32 and PCA9685, with print-to-check templates | New |
| `tools/meshcad/` | Mesh and CAD helper scripts | New |
| `docs/` | Build notes: CAD write-ups, board photos, traps | New |

## Building the firmware

Copy `firmware/EyeMech_PS4/secrets.h.template` to `secrets.h` and fill in your
Wi-Fi details (that file is ignored by git). Then:

```bash
./build.sh            # compile only
./build.sh usb        # compile and flash over USB
./build.sh ota HOST   # compile and flash over Wi-Fi
```

`build.sh` uses the arduino-cli bundled with Arduino IDE 2 on macOS, and the
`min_spiffs` partition scheme so that OTA has two app slots. It needs the
ESP32 Arduino core, the Adafruit PWM Servo Driver library and
[PS4Controller](https://github.com/pablomarquez76/PS4_Controller_Host).
