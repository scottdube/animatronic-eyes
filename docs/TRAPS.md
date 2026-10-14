
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

## KiCad Edge.Cuts made of loose lines scramble under box-select (2026-09-25)

The carrier outline is 23 separate `gr_line`s. A box-select in the PCB editor grabs whichever of them are fully inside
the box, so a drag "moved the board" for some segments and not others; parts were then placed against edges that no
longer existed (J1 25 mm off the real board). Nothing in DRC flags an open outline. Fix was regenerating the lines from
the DXF polygon; the durable fix is the capture → regenerate workflow (`gen/capture_placement.py`), so the outline is
never hand-touched. Alternative rejected: one `gr_poly` outline — KiCad still lets you drag a vertex.

## A mounting hole inside a module's footprint fights every DRC courtyard check (2026-09-25)

The PCA9685 bolts to H3/H4, so the hole footprints sit inside the PCA's body. With a full-body courtyard on the PCA
and a circle courtyard + silk ring on the hole, DRC threw courtyards_overlap, pth_inside_courtyard,
npth_inside_courtyard and four silk collisions — all describing the intended geometry. Resolution: the PCA courtyard is
its two header rows only (the area under the body is usable, the module is on standoffs), the hole footprint has no
courtyard and no silk ring, and the pour keepout stays as a board rule area. Do not "fix" by moving the PCA off the
holes.

## Round pads default to 45° thermal spokes, which land on the sliver between four pads (2026-09-25)

At 2.54 pitch with 0.6 clearance the diagonal gap between a 2×2 pad group leaves a ~0.6 mm copper sliver; a 45° spoke
connects the pad to that sliver and DRC reports "spoke connected to isolated island". `(thermal_bridge_angle 90)` on
the pad fixes it. Separately, `lib_footprint_mismatch` on a rotated generated footprint meant the NPTH pads and text
were written without the footprint angle folded in — KiCad stores pad AND text angles absolute.

## A pour pocket walled off by tracks stays filled if it touches a pad — and then only that pad feeds it (2026-09-25)

Routing the carrier, a +5V stub from the y 10.9 run down to C1.1 and the +5V lane past C1.2 sealed a 12 mm² pocket of
GND pour around C1.2. DRC 0, "0 unconnected", island removal on — and the pocket stayed, because a zone polygon that
touches any pad of its net is not an island to KiCad. The copper in it is fed only through that pad's spoke; for a
module GND pin (PCA pad 6) that means the servo return would have gone through the module. The check is cheap and
DRC does not do it: count `filled_polygon`s in the saved board (one per connected piece of pour) and look at every
extra one's bbox. Fix was moving the C1.1 feed to a diagonal off the lane so the pocket opens west.

## A STEP file's raw points are not where KiCad puts the model (2026-09-26)

I read the PCA9685 STEP's CARTESIAN_POINTs, computed a bounding box, and derived an offset from it. KiCad imported
the model standing on edge, 29 mm off. The raw points sit in each solid's own frame; the assembly placement
(AXIS2_PLACEMENT_3D / ITEM_DEFINED_TRANSFORMATION) is applied on top, and this file's placement rotates the whole
board. The D1 Mini and LM2596 files never showed the problem because ratgdo had already tuned their offsets.
Rule: **find a model's frame by rendering** (`kicad-cli pcb render --side top/right` on a scratch copy of the board
with the `${KIPRJMOD}` path made absolute), try the rotation candidates side by side, then set the offset from a
top-ortho crop at a known feature (mounting hole, pin 1). Rotation order matters too - `(rotate (xyz -90 0 180))`
and `(0 0 180)` then `(-90 0 0)` are different frames - so test the exact triple, don't compose it in your head.
`--pan` gave all-black frames in this KiCad; use `--zoom` and crop with PIL instead.

## DRC "schematic parity" checks more than nets (2026-09-26)

A generated board that passed DRC 0/0/0 threw 61 parity errors the first time Scott ran DRC in the GUI, which has
schematic parity on by default while `kicad-cli pcb drc` does not. Four separate things: no-connect pads must carry
the netlist's `unconnected-(REF-PINNAME-PadN)` net, not no net; the footprint's Description property must equal the
symbol's; Datasheet "" and "~" are different; and the PCB Value must equal the symbol Value (placement.py carried
"12V in", gen_sch said "12V pigtail"). None of these affect copper. Run `kicad-cli pcb drc --schematic-parity` so
the CLI sees what the GUI sees.

## A hand-cleaned DXF is a hypothesis until something physical checks it (2026-09-26)

The carrier outline came from Scott's Fusion export, which he tidied by hand because
of how it transferred. One line moved in the tidy-up and the board carried a kink at
both back corners through routing, DRC, gerbers and the STEP review — none of which can
see a wrong-but-valid outline. The 1.5 mm basswood laser copy laid against the case
found it in a minute. Rule: any outline that was edited after export gets a wood fit
check before the mill runs, and once corrected, the generator's OUTLINE list is the
master, not the DXF.

## Copper-side readings that differ from the top of the same pin (2026-09-28, cause OPEN)
Top of the D1, lead to ground: 3V3 pin 3.3 V, 5V pin 5.2 V. Same pins from underneath, black lead on "ground"
(Scott): −1.9 V and 0 V. A header pin is one piece of metal, so the pin can't differ: the REFERENCE did. −1.9 = 3.3 − 5.2
exactly and 0 = 5V against itself, which is what a reference on the +5V net gives. On a milled board every leftover
copper region looks like pour, and +5V is a copper region separated only by an isolation groove. Hypothesis until the
reference spot is checked against TP5. Rule: clip the black lead to TP5/TP6, not to "the copper nearby".

## An unsoldered GND pin reads as a low 3V3 rail, not as a dead board (2026-09-28, CONFIRMED: soldered, 3.3 V)
With a D1 GND header pin never soldered (a small pad on thermal-relief spokes that didn't look like it needed a joint), the
ESP32 ran normally, Wi-Fi and I2C included, but its 3V3 read 2.7 V against carrier ground, and only on carrier power: on USB
the cable grounds the module. Some other path is carrying the ground return, and the D1's ground sits ~0.6 V off. The
regulator is fine. Before blaming a regulator, measure its output against ITS OWN ground pin, then that ground against TP5.

## DHO914: the front-panel AUTO key is autoscale, not the Auto trigger sweep (2026-09-28)
Pressing AUTO re-sets V/div, timebase and trigger from whatever it finds, wiping a hand-set 1 V / 5 ms / 1.5 V setup.
The Auto *sweep* (draws a trace with no trigger) is in the Trigger menu: Sweep → Auto. Side note: autoscale on the
servo signal pin chose 200 mV/div and 500 ns/div, i.e. it found only noise there — a hint of no pulses, not proof.

## esptool read-flash hard-resets the board into its firmware when it finishes (2026-09-28)
The default `--after hard-reset` means a board plugged in holding BOOT, so it would not run, gets booted
into its firmware anyway once the backup read ends. On the retired DevKit that briefly ran a second eyes host
with the D1's MAC and IP for the ~15 s before the erase. The D1 kept the controller, luckily. On any board that
must not run: pass `--after no-reset` on every esptool call.

## A vertex-to-body check cannot see material the rebuild is missing on a face (2026-10-13)
On the Eye Adaptor every STL vertex sat within 0.04 mm of the native body, but the volume was still 3.7 mm³ short.
Two errors produced no off-body vertices: lug holes cut 0.1 too deep into the gusset, and a missing flat on the
gusset top whose two ends happened to lie on the surfaces that were built. `tools/meshcad/thickdiff.py`, a
column-thickness comparison against a High-refinement STL export of the rebuild, found both. Run both checks.
A rebuild is only done when the vertex max is about 0.001 mm and thickdiff shows only rim-facet noise.

## Cogley's geometry is not exactly symmetric (2026-10-13)
The Eye Adaptor finger-top arc is centred 0.026 mm off the part's mirror plane. Fitting one side and mirroring it
left 0.04 mm at the other end. Fit both sides with a free centre before assuming symmetry. The tangent fillets
then differ per side as well.

## A rectangle's corners fit a circle exactly (2026-10-13)
`profile2d.py` grows an arc over chords of similar length that turn the same way. On the Fork, each arm end
(three ~5 mm sides of a rectangle) came out as one "arc" of R3.5 with residual 0.0000, because the four
corners of any rectangle are concyclic. The fit residual cannot catch it. Fixed with a turn limit: no corner
sharper than 1 rad inside an arc. The four committed plate profiles regenerate byte-identical with the guard.
