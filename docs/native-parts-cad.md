# Native parts and the EyeMech assembly (DONE, 2026-10-13)

Every one of the kit's 15 printable STLs is rebuilt as a native Fusion design: sketches with constraints and
dimensions, extrudes, revolves and chamfers, no mesh. They are assembled from those designs into **"EyeMech
assembly"**. All of it lives in the hub: project Animatronic Eyes, folder Basic EyeMech kit, beside the faceted
conversions. The repo keeps a copy of each part in `hardware/native/<Part> native.f3d` and of the assembly in
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
(`max_mm`, `note`). The assembly is the kit **as the model poses it**, not a kinematic assembly: there are no
joints yet, so nothing moves.

## Open

- Joints (servo horn pivots, lid pivots, the eye gimbal) are not modelled. Add them in Fusion when motion is wanted.
- The STEP's PRODUCT names are timestamps, because each native's root component kept its untitled-document name.
  The 20 instance names are right (`Fork native:1`, ...). Fixing it means renaming 15 root components and saving
  new versions.
