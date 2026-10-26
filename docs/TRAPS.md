
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

## manifold3d: a join across a shared face only is two bodies; a cut flush with a face can be a void (2026-10-13)
`tools/meshcad/xcsg.py` builds specs with manifold3d. Two prisms that only touch on a face stay two shells after
`+`, so joins overlap by 0.5 mm. The mirror case bit on the Servo Block: an Ø3 blind hole whose cut started
exactly on the end face came back as an inverted inner shell (a sealed void of -70.68 mm³), and genus read 4
against the STL's 14 with the volume still right. Every cut now starts 0.5 mm outside the face it enters.
Volume alone does not catch either; compare genus, and `decompose()` when it differs.

## Fusion: a fitted spline handed SketchPoints makes its own end points (2026-10-13)
`sketchFittedSplines.add` given an ObjectCollection holding existing SketchPoints draws through their positions
but creates new fit points, so the originals stay behind, unconnected and free, and the sketch reads "not fully
constrained" while the profile still closes. `fcad.Builder.runs_loop` now joins adjacent run ends with
coincident constraints and deletes the orphans. Spline fit points are fixed (`isFixed`), not dimensioned:
the Servo Block logo is traced artwork with about 290 points.

## A loop helper fed a repeated point draws a zero-length line (2026-10-13)
The Servo Block's front wall loop got `(57.0848, mid_z)` then `(57.0848, 57.7428)` with `mid_z` 57.7428.
The extrude was fine; the zero-length line could not be constrained and the sketch stayed under-constrained
with 0 free points reported. Skip repeated points when a loop is built from parameters.

## Chamfer by picked edge stops where Fusion's edge chain stops; the csg stand-in does not (2026-10-13)
`spec_native.chamfer` with `pick` chamfers the edge through a point plus its tangent chain, and Fusion ends it
cleanly against the next face. The manifold stand-in in `xcsg.py` is a set of cuts that run as far as they are
drawn: on the Main Base the outer chamfer's cut ran past the gusset plane, where the mesh carries on for 0.4 mm
below z 5, and needed a "ch stop" join to match. When the stand-in and Fusion disagree, Fusion's result is the one checked against
the STL.

## The kit's Main Base mesh has a 0.032 mm seam crack; the rebuild fills it (2026-10-13)
A hairline wedge between the block's bottom chamfer and the plate face, 0.032 mm at z 25 closing at z 34.06.
It is a source-CAD seam nobody could print, so `specs/main_base.py` fills it. thickdiff then
shows +40 mm³ of wall-grazing columns at y -23.53; the off-wall number is the one to read.

## zsh does not word-split an unquoted variable (2026-10-13)
`for b in "x0 x1 y0 y1"; do verts.py stl $b; done` passes ONE argument in zsh. Use `${=b}`.

## The eyelids are drawn 20 degrees off the STL axes, and the shell and ring have different centres (2026-10-13)
Top Left Lid: the lip ring's top, underside, tab faces and the past-ear flats are all planes tilted 20 deg about
x, so profile2d on the raw STL found no caps. `tools/meshcad/rotstl.py ... x 20` turns the mesh so they are
axis-aligned; the spec draws in that frame and `FRAME = ("x", -20.0)` turns the body back (xcsg rotates before
the compare, spec_native ends with a Move). In that frame the spherical shell is centred at STL (0, 0.1, 0) but
the lip ring's outside (R19.858) and the ear axis are on the origin: fit each surface's centre separately.
The STL plane y = 0.1 trims only the shell (its face spans z' -17.3..-1.6). Inside the bore at the right ear
sits an R1 pocket along x whose floor is a cylinder about the bore's axis, not a flat end: a slab with a flat
floor would miss by up to 0.9 mm. `section2d` at x 15.3 showed it; xcsg's 2.3 mm³ "extra" blob is what found it.

## The bottom lids are built in TWO frames: 20 deg shell, 18.47655 deg lip (2026-10-13)
Bottom Left Lid: the lip planes' normal fits (0, -0.316917, 0.948453), which is 18.47655 deg, not the top lids' 20.
The shell is still at 20 deg about STL (0, -0.1, 0). The two are a union: ring A (shell frame, R16.5..19.842 about the
shell centre) shows its underside below the lip for |x| < 10.92, and the bore is ring A's wall (normal tilted 1.52 deg)
below z' ~2.06 and ring B's vertical wall above it. Reading the bore triangles one by one settled it; a single
cylinder fit to the band gave a 0.006 mm residual and an axis that made no sense. Specs now have a mid-sequence
`op="rotate"` (xcsg turns the manifold, spec_native adds a Move), and `_mirror` negates its angle.
The ears are R4 squared off toward the ring (profile2d on the x 19.7 cap), and under the ears the ring is NOT cut by
the R4.5 pivot clearance; cutting it there disconnected the ears (xcsg genus 0 / 2 was the tell).

## Fusion's Move "defineAsRotate" rounds the angle (2026-10-13)
`moveFeatures.createInput2(...).defineAsRotate(axis, ValueInput.createByReal(radians(18.47655)))` built an 18.5 deg
Move, and 1.52345 became 1.5 (read back from `MoveFeature.transform`). The shell still landed right because the two
errors sum to 20; ring B's top edge was 0.008 mm off. The top lids' -20 / +20 hid this. `fcad.Builder.rotate_body`
now uses `defineAsFreeMove` with a `Matrix3D.setToRotation` matrix, which is exact (max 0.0012 mm after).
Hypothesis, not tested: it rounds to the angle display precision in the preferences.

## Fusion's Python keeps imported modules between MCP runs (2026-10-13)
The first Bottom Right Lid build was 0.087 mm off and 7 mm³ heavy while xcsg passed the same spec. Its rotate op had
not been negated: `import _mirror` inside the spec got the copy Fusion had cached from the Top Right Lid run, before
`_mirror` learned about rotate ops. Read back from `MoveFeature.transform` (+1.52345 where -1.52345 was due). The
mirrored specs now `importlib.reload(_mirror)`. Anything a spec imports by name has the same exposure; spec_native
already reloads fcad. When Fusion and xcsg disagree on one spec, suspect a stale module before the geometry.

## Fusion's symmetric revolve takes the angle PER SIDE (2026-10-13)
`RevolveFeatureInput.setAngleExtent(True, angle)` (symmetric) swept `angle` each way from the sketch plane, so the
PlaceHolder Eye's 42° / 42° / 92° snap recesses came out 84° / 84° / 184°: 0.667 mm off on the bore wall between
them, 140 mm³ light (a full ring of recess is ~277 mm³, the three sectors ~135). `fcad.SECTOR_SCALE = 0.5` halves it.
Extrudes differ: `setSymmetricExtent(distance, isFullLength)` says which it means; the revolve call has no such flag.

## addByInsert rejects a rotation that is orthonormal only to 7 digits (2026-10-13)
`Occurrences.addByInsert(dataFile, transform, True)` raised "3 : invalid argument transform" on the first lid
placement. placements.json keeps 7 digits, so the fitted rotations' R·Rᵀ is off identity by 4e-9..1e-7, and Fusion's
tolerance is tighter than that. `assembly_native.orthonormal` Gram-Schmidts the rows (moves a point 50 mm out by
~5e-6 mm). The identity and copy+75 placements went in fine, which is what pointed at the rotations.

## A failed MCP script rolls back everything it did (2026-10-13)
That same call had already inserted six occurrences when the seventh raised; afterwards the design had none of the
six (14 occurrences, not 20, after the next batch). The MCP runs a script as one transaction. Re-run the whole
failed range, and count occurrences (or features) after every batch rather than trusting the printed progress.

## A Fusion archive of a referencing assembly holds no part geometry (2026-10-13)
`createFusionArchiveExportOptions("EyeMech assembly.f3z")` wrote `EyeMech assembly.f3z.f3d` (the extension is
appended, not replaced), 61 KB, with no Breps in it: only the top level and its links to the hub designs. Useless
off the hub. The local copy is a STEP export of the root instead (15 solids, 20 named instances). Its PRODUCT names
are the natives' root-component names, which are the untitled-document timestamps they were created under.

## An assembly STL against the kit meshes measures the kit's chord sag (2026-10-13)
Checking the exported assembly's vertices against every kit STL moved by its placement read max 0.21 mm: the native
export puts its vertices on the true curves, the kit mesh's flat triangles sit inside them. The per-part gate runs
the other way (kit vertices to the exact native body), and so must the assembly check: `AS_CHECK` measures each
placed kit vertex against that occurrence's body in place, max 0.0012 mm except the Eye Holder's exempt ring.

## Fusion joints from the MCP (2026-10-14)
- **A `readOnly` script cannot drive a joint:** setting `jointMotion.rotationValue` raises "Cannot modify the design
  from a read-only context". Run drive checks as normal scripts, and put every joint back to 0 at the end.
- **"Cannot perform 'script' while a command dialog is open"** came twice, then cleared on its own. `fusion_mcp_read
  activeCommand` showed only the default Select by the time it was checked. Read activeCommand before asking Scott
  to close anything.
- **Find a hole by its radius, not its axis direction, once a joint is driven:** a lookup for "R1.5 along Y" failed
  as soon as Tilt turned the Fork. Whole-script rollback took the earlier pose's output with it.
- **An as-built joint has no flip.** Its + sense comes from the cylinder face's axis, and a mirrored part's hole
  faces the other way. Record the measured senses rather than assuming them.
- **The Complete Model is a pose, not a mechanism:** its Y-Arm pivot hole sits 1.22 mm off the pin it turns on. Check
  that pins are coaxial before an as-built joint, which keeps whatever pose it is given.
- **A joint value outside its limits is ignored, not clamped.** `rotationValue = 90°` on a joint limited to ±30 left it
  at 0, with no error. A sweep past a limit then quietly tests home. `limits_native.pose` reads every value back and
  raises.
- **An interference result's entity can be the native body** (`assemblyContext` None), which does not say which of two
  occurrences of a part it was. Resolve it by the overlap body's centre against each occurrence's box.

  When both entities are copies of one part (two SG90 horns touching), both resolved to the same name until `who`
  was told to pick a different occurrence for the second.

## A motion-link leader can wander when a joint that carries it moves (2026-10-14)
With the pan horn LEADING Pan L, setting the horn and then Tilt let Fusion re-solve the pan: horn 22 came back 20.34
at tilt +29.5, and from 30 up it ran to its limit (42.08). Setting Tilt first, then the horn, held exactly. With the
horn link suppressed, Pan L itself drifted 20 -> 17.86 the same way. Reversed (Pan L leads, the horn follows), the
horn held to 0.002 deg in either order, at every pan/tilt corner, and that is how all six servo links are built.
Before the servos existed Pan L led Pan R and held to 1e-6, so "the follower holds" is what was measured here, not a
rule about Fusion. Driving a follower still moves its leader, so the servo stays the joint to drive.
- Moving the servos into the holders' own rigid groups (one group per holder, instead of an extra overlapping group)
  changed nothing; it was kept for tidiness, not as the fix.

## The right-hand servos are mirrored meshes: fit them by geometry, not point to point (2026-10-14)
The Complete Model's left and pan/tilt servos are one mesh in one triangle order (4066 tris), so an ordered Procrustes
fit is exact. The right two are mirror copies (3916 tris, det -1, different order). `servo_placements.py` reads every
servo's frame off its geometry instead (case centre -> spline end, spline top, tab underside), and the check is
vertex-to-SURFACE: vertex-to-vertex read 3.4 mm on the right servos, which was only the different tessellation. To
the surface they are 0.1 mm, at the four internal case screws, which are not mirror-symmetric.

## The Complete Model's right lid horns do not meet the right lid links (2026-10-14)
The right links are not in the Complete Model (placements.json mirrors the left ones), and its right horns sit at
+-20 / 160 deg, 6.7 and 7.1 mm from the mirrored links' servo ends. The horns are turned to meet them (mirror of the
left horns' 9.58 / 172.26 deg, to 0.005 mm). The tilt horn is turned 6.71 deg to meet the Y-Arm, which
`joints_native` had moved 1.2 mm onto its pin; it still sits 0.17 mm off radially (horn hole r10.45, arm end r10.28).

## The two lid horns of one eye share a plane and can hit each other (2026-10-14)
Both lid servos of an eye face the same way on shafts 13 mm apart, and a double-arm horn reaches 16.05 mm, so the
arms' sweep circles overlap. At the lid joints' limits (both lids open, or both closed) the two horns intersect
(see docs/native-parts-cad.md for the sweep). Whether the real kit trims an arm is NOT known.

## A joint value set through the API is rounded to the angular display precision (2026-10-14)
`rotationValue = radians(10.25)` read back 10.3 on every joint, linked or not, with
`preferences.unitAndValuePreferences.angularPrecision` = 1. Values a motion link computes are not rounded (Pan L
41.322). The earlier limit sweeps bisected through values like x.125 and read them back to 1e-6, so the precision was
higher then or the rounding is new; which one was NOT established. It is Scott's preference, so it was left alone;
`limits_native` now poses and bisects on that grid (`grid()`).

## A flash dump carries the Wi-Fi passphrase (found 2026-10-26)

`backup/devkit-final-2026-09-28.bin` is a full-chip read, so it includes the NVS partition, and NVS holds the
station SSID and passphrase in the clear. A byte search found the IoT passphrase in it; `board-flash-2026-09-24.bin`
did not have it. `secrets.h.template` keeping the source clean does not keep a dump clean. **Before this repo goes
public, `backup/*.bin` must be purged from history**, not just deleted at HEAD. Full audit:
`~/code/docs/repo-visibility-audit-2026-10-26.md`.
