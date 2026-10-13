# Eye Adaptor: decoded for a native rebuild (IN PROGRESS, 2026-10-13)

Source: `hardware/kit-stl/Eye Adaptor (x2).stl` (7,934 triangles, closed, mm). Faceted copy in the hub:
Animatronic Eyes / Basic EyeMech kit / "Eye Adaptor (x2)", volume 1.5492 cm³. The rebuild must match that
volume and the mesh vertices, as the eyeball did (`docs/eyeball-cad.md`). Tools: `tools/meshcad/`.

Axes as the STL: Z up, base underside z = −6.7. Mirror-symmetric about x = 0 (every plane pairs).
**Nothing is built in Fusion yet.** Values marked ✔ are exact fits (vertex residual 0.000).

| Feature | Value |
|---|---|
| Base disc | R 11.7, z −6.7 → −5.2 (1.5 thick) |
| Side lugs (2) | y −3.1 → +1.0. Walls x = ±3.609 and ±8.359. Profile around the hole axis: inner arc R 2.25 ✔, flat top z = 0.30, outer arc R 2.5 ✔ (flat runs x 5.859 → 6.949) |
| Side lug holes | Ø3.000 ✔, axis along Y at x = ±5.859, z = −1.95 ✔, through the lug |
| Gussets (2) | between side and centre lugs, y −3.1 → about −7.6; outer wall the 45° plane ±0.707x − 0.707y = 7.85; top is R 2.5 ✔ on the side-lug hole axis |
| Centre lug | x ±3.5, y −8.1 → −3.0, top R 3.5 ✔ around the axis x = 0, z = 0 |
| Centre hole | Ø3.000 ✔, axis along Y at x = 0, z = 0, blind from y = −3.0 to floor y = −8.0 (5 deep) |
| Centre ramp | plane −0.857y + 0.514z = 6.84 (about 31° from horizontal), x ±3.5, from y −11.1 at z −5.2 to y −8.1 at z −0.2 |
| Snap fingers (4) | on the rim, rising to z = 2.5; sectors match the eyeball's snap recesses (19°–61°, −61°–−19°, and two fingers in 134°–226° split at 180° for the rib). Barb top flat at z = 0.38 out to r ≈ 12.16. **Not yet decoded:** radii, angular ends, taper, barb ramp |
| −X feature | small half-round on the base/finger at x ≈ −11.7, y ±0.93 (matches the eyeball's Ø1.25 rib at 180°). **Not decoded** |

Next: decode the fingers (inner face x = ±5.76 / −8.02 planes, chamfer n = (0.707, 0, 0.707) d −8.64,
x = ±10.5 walls, y = ±1.5 faces), then build in Fusion as a NEW document "Eye Adaptor native" in the same
hub folder, and check volume plus vertex distances against the faceted body.
