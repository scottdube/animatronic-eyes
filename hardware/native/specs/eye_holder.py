# Eye Holder as axis-aligned extrusions, in the STL's frame. Decoded 2026-10-13 with tools/meshcad (levels: only
# four y levels; profile2d on the y = 0.3 / -2.7 / -7.232 caps; section2d at z 23 / 26.1 / 29.9 for the plan of
# the bar); checked with tools/meshcad/xcsg.py. A 3 mm U plate (legs with R2.5 round ends on the two eye-pivot
# holes, 75 mm apart) plus a trapezoid bar behind its top. Near-symmetric about x = 37.4998, values are the mesh's.
STL = "../../kit-stl/Eye Holder.stl"
TITLE = "Eye Holder native"
DESCRIPTION = "Native rebuild of the kit's Eye Holder (hardware/native/specs/eye_holder.py via spec_native.py)"

Y0, Y1 = -2.7, 0.3               # plate back and front
YS, YB = -7.2, -7.2322           # bar: where the taper ends, and its back face (the 0.032 mm step is the mesh's)
ZB, ZT = 22.1993, 30.0122        # bar bottom (= the plate's inner edge) and top
L, A = "L", "A"

# The STL's two top holes narrow to R1.5 for their last 0.0002 mm (y -7.232 .. -7.2322): a zero-thickness ring
# left by overlapping features in the source CAD, not a counterbore anyone could print. Not modeled; its
# vertices are left out of the vertex check (spec_native.py), the rest of the back face is still checked.
EXEMPT = [dict(box=((cx - 1.6, YB - 1e-4, 26.1058 - 1.6), (cx + 1.6, -7.2319, 26.1058 + 1.6)),
               why="R1.5 ring 0.0002 mm deep at the top hole's back end") for cx in (27.4936, 47.5059)]

FEATURES = [
    dict(name="Plate", op="new", axis="y", lo=Y0, hi=Y1, loop=((70.4366, ZT), [
        (L, (4.563, ZT)), (A, (4.5629, ZB), (-3.25, ZB), 1), (L, (-3.25, 20.1993)), (L, (-2.4983, -0.0925)),
        (A, (0.0, 0.0), (2.4983, -0.0925), 1), (L, (3.25, 20.1993)), (A, (5.25, 20.1992), (5.25, ZB), -1),
        (L, (69.7495, ZB)), (A, (69.7495, 20.1992), (71.7495, 20.2128), -1), (L, (72.5017, -0.0925)),
        (A, (74.9995, 0.0), (77.4983, -0.0925), 1), (L, (78.2495, 20.187)), (L, (78.2495, ZB)),
        (A, (70.4366, ZB), (70.4366, ZT), 1)])),
    # The bar is a y extrusion whose bottom follows the plate's R2 inner fillets (it fills their notch at
    # x 5.03..5.25, ~0.01 mm deep), and the 45-degree-ish plan taper is cut afterwards; a z-extruded trapezoid
    # with a flat bottom misses the STL there by 0.0054 mm. It runs 0.5 mm into the plate: a join across a
    # shared face only is two bodies to manifold3d.
    dict(name="Bar", op="join", axis="y", lo=YB, hi=Y0 + 0.5, loop=((5.0314, 22.1873), [
        (A, (5.25, 20.1992), (5.25, ZB), -1), (L, (69.7495, ZB)), (A, (69.7495, 20.1992), (69.9682, 22.1873), -1),
        (L, (69.9682, ZT)), (L, (5.0314, ZT)), (L, (5.0314, 22.1873))])),
    dict(name="Bar taper L", op="cut", axis="z", lo=20.0, hi=ZT + 1.0, loop=((5.0314, Y0), [
        (L, (21.0314, YS)), (L, (21.0314, YB - 1.0)), (L, (4.0, YB - 1.0)), (L, (4.0, Y0)), (L, (5.0314, Y0))])),
    dict(name="Bar taper R", op="cut", axis="z", lo=20.0, hi=ZT + 1.0, loop=((69.9682, Y0), [
        (L, (71.0, Y0)), (L, (71.0, YB - 1.0)), (L, (53.9682, YB - 1.0)), (L, (53.9682, YS)), (L, (69.9682, Y0))])),
    dict(name="Top hole L", op="cut", axis="y", lo=YB, hi=Y1, circle=((27.4936, 26.1058), 1.75)),
    dict(name="Top hole R", op="cut", axis="y", lo=YB, hi=Y1, circle=((47.5059, 26.1058), 1.75)),
    dict(name="Pivot hole L", op="cut", axis="y", lo=Y0, hi=Y1, circle=((0.0, 0.0), 1.75)),
    dict(name="Pivot hole R", op="cut", axis="y", lo=Y0, hi=Y1, circle=((74.9995, 0.0), 1.75)),
]
