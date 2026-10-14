# Linkages: native rebuilds (DONE, 2026-10-13)

Scott wants to edit the linkages, so the five linkage STLs in `hardware/kit-stl/` are rebuilt as native Fusion
solids. Each is in the hub (Animatronic Eyes / Basic EyeMech kit / "<Part> native") and in
`hardware/native/<Part> native.f3d`. Every body sits in the STL's own frame, so it drops into the kit assembly unchanged.

| Part | Builder | Plate | Volume (native / STL) | Max vertex distance |
|---|---|---|---|---|
| Bottom Lid Link | `plates_native.py` | 2 mm along X, x −16.435..−14.435 | 0.4268 / 0.4268 cm³ | 0.0002 mm (318 vertices) |
| Top Lid Link | `plates_native.py` | 2 mm along X, x −16.435..−14.435 | 0.3294 / 0.3294 cm³ | 0.0002 mm (390) |
| Y-Arm | `plates_native.py` | 3 mm along X, x 0..3 | 1.0732 / 1.0732 cm³ | 0.0001 mm (680) |
| Three-Point Connector | `plates_native.py` | 2 mm along Y, y 5.1..7.1 | 1.2973 / 1.2972 cm³ | 0.0001 mm (764) |
| Fork | `fork_native.py` | 2 mm along Y, y 1.3..3.3, boss to 4.8 | 0.3824 / 0.3824 cm³ | 0.0001 mm (1068) |

`thickdiff.py` (columns run along the plate axis, the sixth argument) shows **0.00 mm³ off-wall** on all five.
The only differing columns graze a profile wall, where the two meshes' facets differ.

## Method

1. `tools/meshcad/plate.py stl toolsdir axis`: classify every triangle as a cap (normal along the axis), a wall
   (normal across it) or other. The lid links, Y-Arm and Three-Point Connector have **zero** "other" triangles,
   so each is exactly one profile extruded through its thickness.
2. `tools/meshcad/profile2d.py stl toolsdir axis level`: the cap's boundary loops, split into lines and arcs.
   Mesh vertices lie on the true curves, so an arc is a run of similar chords turning the same way, with no sharp
   corner, fitted through all its vertices. Arc residuals are ≤ 0.0001 mm. The JSON it prints is what
   `fcad.Builder.loop` takes. Those are `hardware/native/profiles/*.json`.
3. `plates_native.py`: the largest loop is extruded, and full-circle loops are cut as holes.

The sketches hold plain lines and arcs, with no dimensions or constraints. To edit one, add the dimensions you
want to drive in Fusion, or change the JSON and rerun the builder.

## Plate profiles (y, z or x, z in mm)

- **Bottom Lid Link:** a bent bar with R2 ends. Ø2.5 holes at (y, z) (−15.7443, −3.3677) and (−13.5518, 49.3006).
- **Top Lid Link:** R2 ends and R5 bends. Ø2.5 holes at (13.6053, 36.3006) and (15.7249, −3.577).
- **Y-Arm:** Ø3.5 at (8.5765, −6.0053) and Ø2.5 at (10.186, 34.0626). Arcs R4.5, R2.53, R2.56, R2.34, R1.58,
  R3.43 and R3.07.
- **Three-Point Connector** (x, z): Ø3.5 holes at (0, 14.5), (37.4998, 14.4493) and (74.9995, 14.5). R13.0046
  and R6.5046 lobes, R3.25 ends, R4 notch.

## Fork

Every one of its 133 non-cap, non-wall triangles lies on one surface: 0.949·r + 0.316·y = 8.5 about the Y axis.
That is a chamfer, not a free-form surface. The design, with the named constants in `fork_native.py`:

| Feature | Value |
|---|---|
| Plate | y 1.3 → 3.3 |
| Arms | x ±3.3594 → ±8.3594, z −4.9 → 0. Outer arc R8.3594 and inner arc R3.3594, both about the Y axis |
| Arm holes | Ø3.5 at (±5.8594, −1.95): **the Eye Adaptor's lug-hole axis** (that hole is Ø3) |
| Stem | x ±3.3594 up to an R3.3594 round end about (0, 14.5) |
| Boss | R3.3594 about (0, 14.5), y 3.3 → 4.8 |
| Top hole | Ø3 at (0, 14.5), through y 1.3 → 4.8 |
| Chamfer | 0.5 in on the +Y face × 1.5 down the outer wall (y 1.8 → 3.3), along the outer arcs and outer straight sides only. A Fusion chamfer feature, tangent chain |

The chamfer's two distances go to faces in an order the API doesn't document. So `fork_native.py` builds it,
reads back the +Y face's outer radius (it must be 7.8594), and flips the chamfer if it is wrong.
