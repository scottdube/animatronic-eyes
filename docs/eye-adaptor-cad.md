# Eye Adaptor: native rebuild (DONE, 2026-10-13)

Source: `hardware/kit-stl/Eye Adaptor (x2).stl` (7,934 triangles, 3,969 vertices, closed, mm). The faceted copy in
the hub is Animatronic Eyes / Basic EyeMech kit / "Eye Adaptor (x2)", volume 1.5492 cm³.

**Native result:** the design "Eye Adaptor native" sits in the same hub folder and in
`hardware/native/Eye Adaptor native.f3d`, as one body with the same name. It was built by
`hardware/native/eye_adaptor_native.py`, whose helpers are in `fcad.py`. The script opens a new design, builds
the body and prints the checks.

- **Every one of the 3,969 STL vertices is within 0.0009 mm of the body.**
- Volume is 1.5498 cm³. The native body is 0.04% larger than the faceted one, which is the expected sign:
  facets cut the corners off convex surfaces.
- The column-thickness check (`tools/meshcad/thickdiff.py`) finds material where the vertex check is blind.
  Its remaining difference is +0.2 mm³, at the R11.7 rim facets.

Features are a timeline of sketches, extrudes, revolves and combines, so the dimensions can be edited. The
values are plain numbers in the script, not user parameters.

Axes are the STL's: Z up, base underside at z = −6.7. **The part is mirror-symmetric about y = 0, not about
x.** The +X and −X ends differ. All values are in mm.

## Body

| Feature | Value |
|---|---|
| Base disc | R11.7, z −6.7 → −5.2 |
| Side lugs (±X) | y −3.1 → 1.0. XZ profile round the hole axis (±5.859, −1.95): wall x 3.609 up to −1.95, inner arc R2.25 to (5.859, 0.30), flat to 6.949, outer arc R2.5 down to x 8.359 |
| Lug holes | Ø3, along Y at (±5.859, −1.95), **y −3.0 → 1.0**. The gusset closes the lug's last 0.1 mm (−3.1 → −3.0) |
| Gussets | Plan triangle (±3.5, −3.0), (±8.1, −3.0), (±3.5, −7.6); outer face is \|x\| − y = 11.1. Top is a flat from (3.5, −0.024) to (4.0825, −0.191), then R2.5 about the lug-hole axis. The plan reaches y = −3.0, 0.1 past the lug's back face |
| Centre lug | x ±3.5, y −8.1 → −3.0, R3.5 top about (0, 0) |
| Centre hole | Ø3 along Y at (0, 0), blind from y −3.0 to a floor at y −8.0 |
| Centre ramp | YZ triangle (−11.1, −5.2), (−8.1, −5.2), (−8.1, −0.2), over x ±3.5 |

## Snap fingers

Each finger is the ring wall ∩ Q ∩ S, where Q and S are the profiles below.

**Ring wall,** revolved about Z, profile in (r, z):

- From (8.652, −5.2), 45° up to (8.946, −4.906).
- 22.5° line to (10.3413, −4.3279).
- R0.5 fillet about (10.15, −3.8659) to (10.65, −3.8659).
- Up to z 3.0, out to 11.7, down to −5.2.

**+X finger:**

- **Q+** is an XZ profile through all Y.
  - Wall x 5.011, with a concave R0.75 about (5.011, −4.45) to x 5.761.
  - Up to z 0.5, then R2 about (7.761, 0.5) to the top at z 2.5.
- **S+** is a YZ profile over x 5..13.
  - Top z 2.5 except for an arc dipping to z ≈ 0.32. The arc has **centre (0.0264, 7.7818), R7.4598, 0.026 off the
    mirror plane** (fit residual 0.0015 on both sides). It meets z 2.5 at y +5.294 / −5.242.
    A y = 0 centre left 0.04 mm at the ends.
  - Slot |y| < 1.5 with an R1.5 bottom about (0, −3.7).
  - R2 fillets at y ±3.5, tangent to the arc. Their centre heights therefore differ: −1.017 at +y and −0.996 at −y.
    The mesh's slot-wall ends read −1.018 and −0.997.

**−X finger:**

- **Q−:** wall x −7.019 from −5.5 to −5.2, then a 45° chamfer to x −8.019 at −4.2. Up to z 1.0, then R1.5 about
  (−9.519, 1.0) to z 2.5.
- **S−:** the same arc over x −13..−5, with no slot.

**Barbs:**

- Revolve profile: (11.7, −4.753) → (12.199, −1.124) → (12.199, 0.376) → (11.7, 0.376).
- Cut to the sectors 19.5°..60.5°, −60.5°..−19.5° and 134.5°..225.5°, with radial ends.

**Rib slot (−X):** an obround cut through all Z. |y| < 0.925 for x < −11.3654, with a round end R0.925 reaching
x −10.4404. It clears the eyeball's Ø1.25 rib at 180°.

## Method, and what it caught

1. **Decode.** `tools/meshcad/`:
   - `a9` groups coplanar triangles.
   - `a12` gives the (u, z) profile of surfaces extruded along X or Y.
   - `a13` gives the (r, z) profile of revolved surfaces.
   - `fitprof` and the inline circle fits finish the job.
   - Unrolled cylinder sections (`a10`) misdraw the centre ramp, because they draw chords across large
     triangles. Don't trust them for planes.
2. **Vertex check** (`fcad.vertex_check`): distance from each mesh vertex to the native body. It caught the
   gusset ending 0.1 short, and the off-centre finger arc (0.04 mm).
3. **Column-thickness check** (`thickdiff.py`, plus a filter that drops columns grazing vertical walls).
   It caught two errors the vertex check could not see, because the faces involved had no vertices off the
   body:
   - The lug holes cut 0.1 mm too far into the gusset (1.4 mm³).
   - The flat on the gusset tops was missing (1.4 mm³).

   Run it on a High-refinement STL export of the native body: set `EA_STL` before calling `run`.
