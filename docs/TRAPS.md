
## Stop on the page only lasts 20 s (2026-09-24)
`/scene?cmd=stop` sets mode rest and counts as activity, so with idleMode 1 idle restarts after autoIdleSecs
(20 s). Stop is not a hold. To keep the eyes still, set idleMode 0 live (don't Save it). Candidate fix, not
done: have stop set holdRest so auto idle waits for the controller, presence or another command.

## A timed idle run never really ends in automatic mode (read from code 2026-09-25, not observed)
Triangle / page Idle / radar arrival run idle for idleRunMins (5), then drop to rest. But with idleMode 1,
nobody has touched anything for 5 min, so "unattended" is already true and auto idle restarts on the next loop.
The timer only has an effect when idleMode is 2 (manual only). Same root as the page-Stop trap above.

## Sleep is not a safe state for hands in the mechanism (2026-09-25)
Quiet sleep turns the servo pulses off 1 s after the lids close, so every servo goes limp and turns by hand.
Removing or screwing a horn in sleep can move the shaft off the reference. Use 🔧 Service (holds, powered),
or a preset button, never ☾ Sleep. Also: any restart schedules a power-up show 30 s later unless service is on.

## Renaming a settings key breaks string-matched hooks (2026-09-25)
The trim rename cTopL→cLTop silently broke applyLiveSetting, which matched trims by a trailing L/R: the
sliders still saved, but stopped switching the eyes to the preset they trim. Grep every string use of a key
when renaming one.

## A page slider's steps can't land every value (2026-09-25)
upMax steps by 2 from 420, so Scott's "495" saved as 494. Read the value back from /values before recording it.

## The Service NVS flag lives outside the settings table (2026-09-25)
Namespace `scene`, key `service`. Revert/Defaults/Save don't touch it, and it survives a flash. If the eyes
boot "doing nothing" and /status says mode service, that is why: press 🔧 on the page.

## Fusion MCP scripts time out at ~10 s — export, don't iterate (2026-09-25)
Looping `body.vertices.item(i)` or `body.faces` over a 23k-face body dies with "Request timed out"
while the script keeps running in Fusion. Export the body to STL in the scratchpad (one native call,
<1 s) and analyze it locally with numpy. The STL export is in **mm** even though the API works in cm.

## Fusion API: three-point arcs swap start and end (2026-09-25)
`sketchArcs.addByThreePoints(start, mid, end)` returns an arc whose `endSketchPoint` may be the
point you passed as *start* (arcs are stored CCW). Chaining `prev.endSketchPoint` after an arc then
continues from the wrong corner and the profile splits into several. Pick the sketch point nearest
the intended next point instead of trusting start/end.

## Fusion API: a symmetric revolve angle is per side (2026-09-25)
`setAngleExtent(True, angle)` sweeps `angle` on EACH side of the sketch plane, so 42° gave an 84°
cut. Pass half the wanted width. And `setAngleExtent` on an existing RevolveFeature fails with
"Didn't roll editing feature back" even after `timelineObject.rollTo(False)` — delete and recreate.

## KiCad 10 file versions differ per file type (2026-09-25)
A generated `carrier.kicad_sym` with the schematic's `(version 20260306)` fails to load and ERC reports
"symbol library not found at <path>" even though the file is there — "not found" means "did not parse".
Symbol libraries are `20251024` (copy the header of a stock `.kicad_sym`); schematics `20260306`; boards
`20260206`; footprints `20241229`. `kicad-cli sym upgrade --force` / `fp upgrade --force <DIR>` is the
validator — `fp upgrade` takes a library directory, not a `.kicad_mod`, and "fails" on a single file.

## ERC endpoint_off_grid: place symbols on 1.27 mm multiples (2026-09-25)
52 warnings from a generated schematic whose symbol origins were round numbers. Every symbol origin, wire
end and label must be a multiple of 1.27; pin ends are then on grid by construction.

## Single-sided D1 Mini: the pin you want is usually unreachable (2026-09-25)
Inner header columns can only leave the module through its middle and out past the last pin row; outer
columns leave sideways, and a vertical lane beside the module blocks every pad facing it. Pick the pins
from the routing, not the datasheet defaults — here I2C went to IO25/IO27 and the ADC to IO36.
