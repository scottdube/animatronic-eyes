# Native parts and the EyeMech assembly (DONE, 2026-10-13)

Every one of the kit's 15 printable STLs is rebuilt as a native Fusion design: sketches with constraints and
dimensions, extrudes, revolves and chamfers, no mesh. They are assembled from those designs into **"EyeMech
assembly"**. All of it lives in the hub: project Animatronic Eyes, folder Basic EyeMech kit, beside the faceted
conversions. Since 2026-10-14 it also carries the six SG90 servos and their horns (below), decoded from
`Complete Model.stl` since the kit ships no servo STL. The repo keeps a copy of each part in `hardware/native/<Part> native.f3d` and of the assembly in
`hardware/native/EyeMech assembly.step`.

Earlier write-ups: `eyeball-cad.md` (the eyeball, by hand), `eye-adaptor-cad.md`, and `linkages-cad.md` (the five
linkages, whose builders came before the spec format below).

## The parts

The gate for every part: each STL vertex lies within 0.002 mm of the native body (`fcad.vertex_check`), and every
sketch is fully constrained.

| Part | Built by | Max vertex distance | Sketches / dimensions | Notes |
|---|---|---|---|---|
| Eye Adaptor | `eye_adaptor_native.py` | 0.0009 mm | constrained by `constrain_docs.py` | `eye-adaptor-cad.md` |
| Bottom Lid Link, Top Lid Link, Y-Arm, Three-Point Connector | `plates_native.py` + `profiles/*.json` | 0.0002 mm | same | `linkages-cad.md` |
| Fork | `fork_native.py` | 0.0001 mm | same | a real chamfer feature |
| Sub Base | `specs/sub_base.py` | 0.0002 mm | 15 / 87 | |
| Eye Holder | `specs/eye_holder.py` | 0.0005 mm | | EXEMPT: an R1.5 ring 0.0002 mm deep in the mesh |
| Main Base | `specs/main_base.py` | 0.0002 mm | 41 / 225 | fills the mesh's 0.032 mm seam crack (TRAPS) |
| Servo Block | `specs/servo_block.py` | 0.0001 mm | 18 / 112 | logo = three fitted splines, fixed, not dimensioned |
| Top Left Lid | `specs/top_left_lid.py` | 0.0012 mm | 16 / 56 | drawn at 20°, one Move back to the STL frame |
| Top Right Lid | `specs/top_right_lid.py` | 0.0012 mm | 16 | the Top Left spec mirrored by `_mirror.py` |
| Bottom Left Lid | `specs/bottom_left_lid.py` | 0.0012 mm | 14 | two drawing frames, 20° and 18.47655° |
| Bottom Right Lid | `specs/bottom_right_lid.py` | 0.0012 mm | 14 / 57 | Bottom Left mirrored |
| PlaceHolder Eye | `specs/placeholder_eye.py` | 0.0001 mm | 7 / 38 | sector revolves; tilted, offset-axis R16 shell |
| SG90 | `specs/sg90.py` | 0.1000 mm | 9 / 35 | bought part, SIMPLIFIED: plain R2.45 spline, labels off; GATE_MM 0.11 |
| SG90 Horn | `specs/sg90_horn.py` | 0.0750 mm | 17 / 36 | double arm, Ø1.2 holes r4.45..14.45; plain socket; GATE_MM 0.11 |

The two SG90 meshes were cut out of `Complete Model.stl` (the tilt servo's copy, in its own servo frame) into
`hardware/kit-stl/from-complete-model/`. They are bought parts, so the spline teeth and the 0.1 mm stickers are left
off; the spec sets `GATE_MM` to say how far it departs from the mesh, and everything that locates the servo (case,
tabs, tab holes, shaft position and height) is within 0.0001 mm.

Every body sits in its STL's own frame, so the assembly placements apply to the natives unchanged.

## The spec method (`hardware/native/specs/*.py` → `spec_native.py`)

A spec is a Python file with `STL`, `TITLE`, `DESCRIPTION`, optionally `FRAME` and `EXEMPT`, and a `FEATURES` list.
Each feature is one sketch plus one operation, in order:

- `op` is `new`, `join` or `cut`; `axis` is x, y or z, the sketch plane normal; `lo`/`hi` give the extrude span along
  it.
- The profile is `loop=(start, [("L", pt), ("A", centre, end, ±1), ...])`, `circle=(centre, r)`, or
  `revolve=dict(centre, loop, a0=, a1=)`, a half-section (r, w) turned about the axis through `centre`. A full turn
  is the default. **a0..a1 gives a sector, about Z through the origin only.** It is built on a plane at the mid angle
  with a symmetric extent, and Fusion takes that angle per side (TRAPS).
- `op="rotate"` (axis, deg) turns everything built so far. The lids are drawn in their own tilted frame and turned
  in stages; `FRAME` adds one closing Move back to the STL frame.
- `op="chamfer"` with `face`/`skip` planes or `pick` points becomes a Fusion chamfer feature.
- `_mirror.py` derives a mirror-image part's spec from its twin (the Right lids), so every dimension lives in
  one file.

The pipeline for one part:

1. Decode with `tools/meshcad` (section2d, profile2d, levels, circle fits; see its README).
2. `tools/meshcad/xcsg.py <spec> tools/meshcad` builds the spec with manifold3d and compares it to the STL offline:
   missing/extra volume and genus. Accept when only slivers remain.
3. Run `spec_native.py` through the Fusion MCP with `SP_SPEC=<slug>` and `SP_STL=<out.stl>`. It builds, runs
   `fcad.constrain_all`, and runs the vertex check.
4. `tools/meshcad/thickdiff.py <kit stl> <out.stl> tools/meshcad` compares column thickness. The differences
   should graze walls or be chord effects.
5. Run again with `SP_SAVE=1`. It saves "<Part> native" to the hub folder and writes the `.f3d`. It refuses if the
   gate fails.

**To edit a part:** change its spec and rebuild with SP_SAVE. The hub design gets a new version, and the assembly
picks it up as a reference update. Editing the hub design directly in Fusion also works, but then the spec and
the design disagree.

## The assembly (`hardware/native/assembly_native.py`)

`tools/meshcad/placements.py` fitted each of the 20 part occurrences against `Complete Model.stl` and wrote
`hardware/native/placements.json`. The kinds:

- **identity:** the part's STL already sits in place.
- **copy+75:** the right eye's copy of an (x2) part, moved +75 mm in x. The model mirrors the left eye instead, which
  only a mirrored print could be.
- **lid:** a rotation about X through the eye centre.
- **plate:** a rotation about X plus a Y/Z shift.
- **mirror / rlid:** the right-eye lid links and lids, composed into rigid motions.

Every matrix has det +1, so no occurrence is reflected.

`assembly_native.py` inserts each occurrence as a **reference** (`addByInsert(dataFile, transform, True)`) to its
"<Part> native" hub design, so part edits reach the assembly. Main Base is grounded. Env (through the MCP):

- `AS_NEW=1`: open a new design.
- `AS_RANGE=a:b`: insert `placements[a:b]`. Batches of about 6–9 run in seconds; a failed batch rolls back whole.
- `AS_CHECK=n`: vertex check every occurrence.
- `AS_SAVE=1`: save as "EyeMech assembly".
- `AS_STEP=1`: export the local STEP.

**Check (AS_CHECK=10, 2026-10-13):** every 10th vertex of each kit STL, moved by its placement, measured against
that occurrence's body in place. Max 0.0001–0.0012 mm on 19 of 20, the same as each part's own gate. The Eye Holder
reads 0.2501 mm at part (46.045, −7.232, 26.448), inside its spec's EXEMPT box: the ring artifact, not placement. So
every occurrence has the right part, the right transform and a live reference.

What the placements are worth: each fits the coarse `Complete Model.stl` to 0.27–0.43 mm (chord error of that mesh).
Exceptions: the Eye Adaptor R and PlaceHolder Eyes (2.1–3.0 mm, where the model's mirrored eye differs from a
printable copy) and the right lid links, which the model leaves out. Read those numbers in `placements.json`
(`max_mm`, `note`). The placements are the kit **as the model poses it**; `joints_native.py` adds the motion on
top of that pose (below).

## Joints (`hardware/native/joints_native.py`, 2026-10-14)

The pivots were read off the placed parts' cylinders, not assumed. Every pin runs through a Ø3 hole in the part that
holds it and a Ø3.5 clearance hole in the part that turns on it. All joints are **as-built revolutes**, so home
(every joint at 0) is the Complete Model pose. Gaze is −Z, Y is up, and the right eye is at +X.

| Joint | Turns | On | Axis | + direction (measured) |
|---|---|---|---|---|
| Tilt | Sub Base + Eye Holder (rigid group) | Main Base pins, inner walls x 20–23 / 52–55 | X through both eye centres | eyes look up |
| Pan L, Pan R | Eye Adaptor + Fork + eye (rigid group, two lug pins) | Eye Holder's vertical pin | Y through each eye centre | toward −X; Pan R follows Pan L 1:1 |
| Top Left Lid / Top Right Lid | the lid | Main Base pins (not the Sub Base: lids do not follow tilt) | X through eye centres | opens / closes |
| Bottom Left Lid / Bottom Right Lid | the lid | Main Base pins | same | closes / opens |
| Three-Point Connector | the connector | Fork L tail pin (z 14.5) | Y | counter-rotates against Pan L |
| Y-Arm | the Y-Arm | Sub Base pin at (y 10.47, z 0) | X | counter-rotates against Tilt |
| Top/Bottom Lid Link L/R | the link | its lid's Ø2 hole | X | counter-rotates against its lid |

Rigid groups: Main Base + Servo Block (+ five SG90s since `servos_native.py`), Sub Base + Eye Holder (+ the pan
SG90), and each eye's Adaptor + Fork + PlaceHolder Eye. Main Base is grounded.

- **The lid signs are mixed** because the right-hand lids are mirrored parts whose holes face −X, and an as-built
  joint has no flip. The kit's lid servos are mirrored the same way (closed: 2=400, 3=240, 4=240, 5=400).
- **Couplers counter-rotate:** Fusion solves a tree, not the real four-bar loops. (The horns now exist and drive
  the mechanism through motion links, below, but the couplers are still not jointed to them.) Each coupler is pinned at its mechanism end and motion-linked −1:1 to the joint it rides on, so it keeps
  its orientation and its servo end slides past where the horn would be. For the connector this is exact, because
  the eyes and connector form a parallelogram; for the Y-Arm and lid links it is an approximation at the horn end.
- **The Y-Arm was moved 1.22 mm** (0, −0.2405, −1.1969) onto its Sub Base pin before jointing. The Complete Model
  poses its pivot hole that far off the pin, and an as-built joint keeps the pose it is given. `placements.json`
  carries the moved matrix, so AS_CHECK still holds (Y-Arm 0.0001 mm).

**Verified (JN_DRIVE, 2026-10-14):**

- Pan L 25° turns all six eye-group occurrences 25°. The connector moves 6.277 mm without turning, and the right
  Fork's tail pin stays within 0.0005 mm of its connector hole axis in every pose tried.
- Tilt 15° turns the Sub Base, Eye Holder, connector and both eyes 15°. The Y-Arm moves 2.733 mm without turning
  (2·10.47·sin 7.5° = 2.733).
- Pan −25 with Tilt −15 composes to 29.09°, as expected for those two axes.
- The lids turn 20°; their links translate 5.60 mm and turn ≤ 0.0008°.
- Every pose returns to home within 1.4e-5 cm.

## Limits and collisions (`hardware/native/limits_native.py`, 2026-10-14)

Each limit is a measured stop. A sweep drives the joint out from home until Fusion's interference analysis reports any
overlap between any two of the 20 bodies, then bisects to 0.1°. At home nothing overlaps.

| Joint | Limits (deg) | What stops it |
|---|---|---|
| Pan L, Pan R | −44.8 .. +41.9 | the eye's rim reaches the Eye Holder (both directions) |
| Tilt | −32.3 .. +29.5 | up: Sub Base reaches Main Base. Down: connector reaches Y-Arm, **approximate** (the Y-Arm's angle is the counter-rotation stand-in); without the Y-Arm the next stop is the connector reaching the top lids at −46.5 |
| Top Left / Bottom Right Lid | −25.7 .. +24.4 | closed: both lids of an eye meet, lip to lip (0 → 0.94 mm³ in 0.1°) when closing together |
| Top Right / Bottom Left Lid | −24.4 .. +25.7 | open: the most both lids can open **together** at any pan with tilt 0 (below) |

Lid opening, measured:
- A lid alone opens further: top 46.5° (reaches the connector), bottom 53.3° (reaches the top lid's back edge).
- Both lids of an eye opening together meet at the back at 26.6°.
- With pan at −44.8° and both lids opening, the connector reaches the top lid at 24.4°, which sets the open limit.

Couplers have no limits; they follow their motion links.

**Verified clear (100 poses, every value read back from its joint):**
- At tilt 0 and at +29.5: pan −44.8 / 0 / +41.9 × each of the four lids at its open or closed limit (96 poses).
- At tilt −32.3: closed lids at all three pans, and everything at home.

These are corners only, not the interior.

**The one collision limits cannot prevent: eyes down with the top lids open.** The connector turns with Tilt about
the same axis the lids turn on, so it reaches the top lids when the lid opening minus the tilt passes a threshold that
depends on pan. Measured tilt-down still clear:

| Top lids | Pan −44.8 | Pan 0 | Pan +41.9 |
|---|---|---|---|
| open (24.4) | 0.0 | −22.1 | −3.0 |
| home (0) | −24.4 | −32.3 (limit) | −27.4 |
| closed | −32.3 (limit) | −32.3 | −32.3 |

The kit firmware moves the lids with the eyes' up/down ("lids track Y" in CLAUDE.md). That is probably why (hypothesis,
not tested on the hardware). The alternative was a limit box with no collision anywhere, but it allows almost no
tilt-down.

How the limit angles relate to servo commands is not known: the horn angle per limit is (limit / ratio, below),
but the SG90's µs per degree and the kit's home command are not measured.

**Lid horns collide with each other (2026-10-14, with the servos in).** The two lid horns of one eye sit in the same
plane, 13 mm apart:
- Both lids opening together: the horns meet at **10.1° of horn** (≈ 9° of lid; the open limit is 24.4).
- Both closing together: clear to horn 27.2, hit at 27.8 (the closed limit is ≈ horn 28.6).
- Each lid alone: clear to ~21° toward the other horn.

Every one of these hits involves exactly one arm that carries no coupler: opening, the top horn's link arm (−Y)
reaches the bottom horn's spare arm (+Y); closing, the top horn's spare arm reaches the bottom horn's link arm. All
couplers sit on arm −Y. **Hypothesis, not checked on the hardware:** a single-arm or trimmed horn on the lid servos
clears both, and the real build has one. The horn limits below are therefore the mechanism's, not the horns'.

Pan and tilt servos at their extremes: clear. Tilt −32.5 with pan ±44.5 shows the connector against the top lids
(0.8 / 0.18 mm³), the coupled collision in the table above.

## Servos and horns (`hardware/native/servos_native.py`, 2026-10-14)

`tools/meshcad/servo_placements.py` fitted the six servos and horns in `Complete Model.stl` and wrote placements.json
rows 20–31 (`kind` servo, `stl` from-complete-model). Each servo frame is read off the geometry: Z from the case
centre to the spline, origin on the shaft 6.7 above the tab underside, +Y from the case centre to the shaft. A
point-to-point fit was rejected: **the right-hand servos and horns are mirrored meshes with their own triangle
order**, so an ordered fit only works on the left two and the pan/tilt pair. Checked vertex-to-surface against the
extracted STLs: left, pan and tilt servos 0.0001 mm; right servos 0.1 mm (only at the internal case screws, where the
mirrored mesh differs); horns as placed 0.0001 mm.

Occurrence k of "SG90 native" / "SG90 Horn native" is PCA9685 channel k−1:

| Servo | Held by (measured nearest body) | Horn angle | Drives |
|---|---|---|---|
| 0 Pan | Sub Base (0.4 mm; 1.7+ to all else), so it tilts with the eyes | 0 (as in the CM) | Three-Point Connector at r14.45 |
| 1 Tilt | Main Base + Servo Block (0.3 mm each) | −6.48 (turned −6.71) | Y-Arm at r10.45 |
| 2 Top Left Lid | same | 172.26 (as in the CM) | Top Lid Link L at r14.45 |
| 3 Bottom Left Lid | same | 9.58 (as in the CM) | Bottom Lid Link L at r14.45 |
| 4 Top Right Lid | same | 187.69 (CM had 160) | Top Lid Link R at r14.45 |
| 5 Bottom Right Lid | same | −9.58 (CM had 20) | Bottom Lid Link R at r14.45 |

Horn angle is about the shaft, 0 = arms along servo Y; the horn is symmetric, so only mod 180 matters. **Three horns
were turned** because the Complete Model leaves those linkages open: its right lid horns sit at ±20°, 6.7 and 7.1 mm off
the right links (which the model leaves out; placements.json mirrors the left ones), and the tilt horn missed the
Y-Arm once the Y-Arm was moved onto its pin. Closures after turning: lids 0.005–0.012 mm, pan 0.0000; **tilt 0.17 mm,
radial**: the Y-Arm hole sits at r10.278 from the shaft, the horn hole at r10.45. Not chased further: the Y-Arm's own
pose is already a 1.22 mm correction of the CM.

The build (env as in the file header):
- **SV_BUILD:** each servo goes into its holder's rigid group (the old group is deleted and remade; an occurrence in
  two overlapping groups is legal, but a merged one did not change the drift below and is easier to read). Each horn
  gets an as-built revolute on the servo's R2.45 shaft face.
- **SV_SOLVE:** a motion link is linear and a four-bar is not, so each ratio is the least-squares slope of the solved
  four-bar (horn hole → coupler of fixed length → mechanism pin) at 9 angles across the mechanism's limits.
- **SV_LINK:** links **mechanism → horn**, ratio below, horn limits = mechanism limits / ratio.

| Servo | Mechanism ° per horn ° | Worst departure of the linear link |
|---|---|---|
| 0 Pan | +0.99570 | 0.049° |
| 1 Tilt | +0.98207 | 1.196° (at tilt −32.3) |
| 2 / 4 Top lids | −0.89870 / −0.89876 | 0.434 / 0.439° |
| 3 / 5 Bottom lids | −0.90565 / −0.90566 | 0.474 / 0.475° |

Signs are Fusion's joint directions, not the hardware's.

**Why mechanism leads:** with the horn as leader, setting the pan horn and then Tilt let the pan wander up to 1.7°,
and to its limit from 30° up; setting tilt first held. Reversing every link to mechanism → horn made both orders hold
exactly (verified). See TRAPS.

**Verified (SV_DRIVE, 2026-10-14):** a real coupler of fixed length would have to stretch ≤ 0.003 mm (pan, and lids
at 10–20°), ≤ 0.11 mm at the lid extremes, 0.10–0.20 mm on tilt: that is the linear link's error. The drawn couplers
(still the counter-rotating stand-ins) end, measured across the shaft axis, 0.006 mm (pan, exact: parallelogram),
0.15–0.23 mm (lids at horn +10°) and 0.56 mm (tilt at horn +20°) from the horn hole; along the shaft they also sit
~2 mm off the horn's mid-plane (straight-line distances read 2.0–2.6 mm; that offset is most of it). Examples: Servo 2 +10° → Top Left Lid −8.987°; Servo 1 +20° → Tilt
+19.641°.

Saved to the hub (32 occurrences, 19 joints, 4 rigid groups, 13 motion links) and re-exported to the local STEP.

## Open

- Map servo commands (kit X 220–440, Y 250–500, lid closed 2=400 3=240 4=240 5=400) to joint angles. The horn
  geometry and ratios are in; still missing are the SG90's µs per degree and which command is home (the CM pose).
- Do the real lid horns have one arm, or a trimmed spare arm? The model's double-arm horns collide (above).
- Interior poses are not swept, only corners.
