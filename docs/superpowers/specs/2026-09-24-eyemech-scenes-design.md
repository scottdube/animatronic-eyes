# EyeMech scenes, lid sliders and radar trigger

Approved by Scott in chat on 2026-09-24. This is step 3 of the OTA/settings/scenes work
(steps 1–2 are in `CLAUDE.md`).

## Who drives the eyes

Priority: **controller > playback > alive idle > rest**. Sleep is a held
lids-closed rest. Every source produces the same frame the controller does
(stick-space x/y -128..127, blink, lid trim), and it goes through the kit's servo
math, which is not changed except for the two lid settings below.

- **Takeover:** a stick past the deadzone (16), Cross/Square, or the D-pad stops
  playback, idle and sleep at once. Triangle, Circle and Share are scene
  commands, not a takeover. They only reset the unattended timer.
- **Recording** is not a driving mode: it is the controller driving while
  a recorder captures it. The page shows it as its own mode.

## Alive idle

- Setting `idleMode`: **Off**, **Automatic** (starts after `autoIdleSecs` with no
  takeover input, including when no controller is connected) or **Manual only**.
  Triangle or the page starts and stops it in Automatic and Manual. A manual start
  runs for `idleRunMins` (0 = until stopped). An automatic start runs until takeover.
- Generator: a gaze target is picked every `glanceSecs` × (0.5–1.5). 70% of targets are
  small (30% of `glanceRange`), and 30% are full `glanceRange`. The eyes move fast toward it
  (τ ≈ 60 ms, a saccade), with a small random drift between glances. Blinks follow a Poisson process at
  `blinkRate`/min, 150 ms each, with 15% doubles.

## Record and replay

- One recording, stored in the `spiffs` data partition (128 KB, raw
  `esp_partition_*`, no filesystem, no heap). 50 Hz frames of 4 bytes (x, y, flags,
  trim), with a 256-byte header written at the end. Maximum ≈ 654 s (10.9 min).
- Share or the page starts/stops recording, and Circle or the page plays/stops. Starting a recording erases
  the partition first (~1.3 s, eyes hold still). A recording stops at max length or on
  controller disconnect. Playback runs once, restores the lid trim from before it started,
  and then hands back (to idle when started as "play then idle").

## Lids

- `lidMin` (280 → 250), **Top lid max open**: the upper lid's open limit, and
  the whole upper lid opens by `280 - lidMin` extra. Scott's original sketch used 250 on
  this mechanism.
- `lidFollow` (0–100%), **Lid follows eyes**: 100 = the kit's behaviour, and 0 = lids
  hold the mechanical-centre position whatever the gaze.

## Radar trigger

- Home Assistant calls `POST /presence?state=on|off` from the shop bench radar
  (`binary_sensor.sln_shop_bench_presence`, `esphome/sln-shop-bench.yaml`).
  An HA token on the eyes and ESPHome→eyes calls were both rejected (see the chat record in
  `CLAUDE.md`).
- The eyes decide what that means. `arriveAction`: nothing / idle / play then
  idle, and it always wakes from sleep. `emptyAction` after `emptyMins`: keep going / rest /
  sleep. Presence actions are skipped while the controller has been used within
  `autoIdleSecs`. Sleep blocks automatic idle until presence or takeover.
- Needs a fixed IP for the eyes in UniFi (Scott).

## Light bar

Blue = controller/rest, green = idle, magenta = playing, **flashing** red =
recording, dim = asleep. Because Scott is colourblind, the page states the mode in words with a symbol
(● live, ∿ idle, ⏺ recording, ▶ playing, ☾ asleep, ○ rest).

## Build order and testing

1. Alive idle: tested from the page and `/status` with no controller. Scott checks the look.
2. Lid sliders: Scott drags them and watches for a straining servo.
3. Record and replay: Scott records with the controller, and playback is checked on serial and by eye.
4. Radar: HA package in `sln-ha-config`, verified on the NUC. Test by walking up to the bench.

## Revision 2026-09-25: the show cycle (supersedes automatic idle)

Automatic idle ("idle whenever unattended") ran 24/7 and Scott powered the eyes off: the servos are loud.
His stated use: walk in, 30 s later the eyes wake and do a short show (2–3 min), then sleep while he is in
the lab. Another show on a return after the lab was empty a while, and every so often while he is there.
Longer runs on demand ("extended play", HA voice).

- **Show** = alive idle for `showSecs` (150), then **sleep**. Triangle, page Show, and voice "show" start one.
- **Arrival** (radar on after `emptyMins` (5) empty, or power-up) → show after `arriveDelay` (30 s).
  Leaving during the wait cancels it. `arriveAction` still picks idle or recording-then-idle.
- **Periodic**: every `showEvery` (60) min while present, if the eyes are resting or asleep. 0 = off.
- **Extended**: `extendMins` (20), from the page or HA. `/scene?cmd=extended`.
- **Controller**: after you let go, the eyes go back to sleep after `handsOffSecs` (20).
- **Stop** (page) = rest, eyes open, until something else happens (tuning uses this).
- **Quiet sleep** (`sleepQuiet` 1): 1 s after the lids close, all six channels go full-off; no hum.
  Risk to check: lids sagging open with no holding torque.
- `idleMode` 0 = no shows (eyes rest open, the old behavior), 1 = automatic, 2 = on demand only.
- Removed: autoIdleSecs, idleRunMins, emptyAction, and the holdRest mechanism (nothing automatic runs
  unprompted any more, so there is nothing to hold off).
- `/status` gains `nextShow` and `showLeft` (seconds, -1 = none); the page shows both.
