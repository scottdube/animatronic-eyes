# Eyeball CAD — the STL decoded into a native Fusion solid (2026-09-25)

Fusion document **"Eye model"** holds the Cogley eyeball STL, converted with *Convert Mesh*
(Faceted): body **"Eye Ball"**, 22,988 planar faces. It IS a solid, but a faceted one — every
operation drags, and nothing on it selects as "the sphere". Prismatic conversion needs the Design
extension, which this licence does not have. So the body was rebuilt as a native revolve,
**"Eye Ball native"**, in the same document, and the faceted body hidden (not deleted) beside it.

All dimensions below were **measured off the mesh** (exported to STL, sections ray-cast in numpy),
not read from Cogley's source. Axis = Z, back face at z=0, front pole at z=22.5 (less the dish).

| Feature | Value |
|---|---|
| Outer sphere | R 15.0, centre on axis at z=7.5 (fit scatter 0.09 mm) |
| Back cut | flat at z=0, outer radius there 12.99 |
| Rear bore | Ø24.0 (r 12.0), from z=0 to the ceiling at z=14.6 |
| Front pocket | Ø3.4 (r 1.7), floor at z=16.5 |
| Iris dish | concave sphere R 8.5, centre on axis at z=26.333; rim at r 6.60 / z 20.97; meets the pocket at z 18.0 |
| Keying rib | half-round, Ø1.25, on the bore wall at 180° (−X), from the back face up to z=6.83 |
| Snap recesses (3) | in the bore wall, r 12.0→12.79; floor z=6.83, back wall to z=8.70, then a ramp back to r 12.0 at z=14.175. Sectors: 19°–61°, −61°–−19°, 134°–226° (the −X one is 92° wide, the others 42°) |

Check against the faceted body: volume 4.8441 vs 4.8446 cm³ (0.5 mm³), 202 sampled mesh vertices
within **0.01 mm** of the native solid, point probes on both sides of every recess edge agree.

Timeline features added: `Eye profile` + `Revolve2` (the shell), `Eye rib` + `Extrude2`,
then `Recess ±40 / 180` plane + profile + cut. Body2 (Scott's Ø12.2 × 5 disc at z 16.05–21.05)
was already there and is untouched. **The document was left unsaved.**
