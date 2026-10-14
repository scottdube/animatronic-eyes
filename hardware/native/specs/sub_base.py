# Sub Base as axis-aligned extrusions, in the STL's frame. Decoded 2026-10-13 with tools/meshcad (levels, secplot,
# profile2d on the y = -15.532 / -7.532 and x = 23.459 / 51.541 caps); checked with tools/meshcad/xcsg.py.
# Near-symmetric about x = 37.4998 (the two Ø3 holes sit 10.0062 either side), so values are the mesh's, per side.
STL = "../../kit-stl/Sub Base.stl"
TITLE = "Sub Base native"
DESCRIPTION = "Native rebuild of the kit's Sub Base (hardware/native/specs/sub_base.py via spec_native.py)"

YB, YP, YF = -15.5322, -11.5322, -7.5322        # back face, back plate front, top block front
XL, XR = 23.4588, 51.5407                        # arm outer faces
TL, TR = 26.4588, 48.5407                        # arm inner faces (3 mm arms)
L, A = "L", "A"


def chamfer_csg(x_in, sgn, y_end):
    """Stand-in for the 1 mm chamfer round an arm's inner face: two straight cuts along the arm, a half cone
    round its R5 end. sgn = +1 for the left arm (inner face toward +x)."""
    x0, x1 = x_in - sgn * 1.0, x_in + sgn * 0.5
    out = []
    for zs in (1, -1):
        out.append(dict(name="ch", op="cut", axis="y", lo=YP, hi=y_end, loop=((x0, 5.0 * zs), [
            (L, (x_in + sgn * 0.5, 5.0 * zs)), (L, (x_in + sgn * 0.5, 3.5 * zs)), (L, (x0, 5.0 * zs))])))
    w0, w1 = sorted((x0, x1))
    pts = [(5.0, x0), (3.5, x1), (6.0, x1), (6.0, x0)] if sgn > 0 else [(5.0, x0), (6.0, x0), (6.0, x1), (3.5, x1)]
    out.append(dict(name="ch end", op="cut", axis="x", lo=0, hi=0,
                    revolve=dict(centre=(y_end, 0.0), pts=pts, a0=-90.0, a1=90.0)))
    return out


FEATURES = [
    dict(name="Back plate", op="new", axis="y", lo=YB, hi=YP, loop=((50.9682, 30.0122), [
        (L, (24.0314, 30.0122)), (L, (24.0314, 18.8374)), (L, (28.9998, 13.5996)), (L, (28.9998, 6.5)),
        (L, (27.4998, 5.0)), (L, (XL, 5.0)), (L, (XL, -5.0)), (L, (27.4998, -5.0)), (L, (28.9998, -6.5)),
        (L, (28.9998, -10.4007)), (L, (30.4998, -11.9007)), (L, (44.4998, -11.9007)), (L, (45.9998, -10.4007)),
        (L, (45.9998, -6.5)), (L, (47.4998, -5.0)), (L, (XR, -5.0)), (L, (XR, 5.0)), (L, (47.4998, 5.0)),
        (L, (45.9998, 6.5)), (L, (45.9998, 13.5996)), (L, (50.9682, 18.8374)), (L, (50.9682, 30.0122))])),
    dict(name="Top block", op="join", axis="y", lo=YP, hi=YF, loop=((50.9682, 30.0122), [
        (L, (24.0314, 30.0122)), (L, (24.0314, 18.8374)), (L, (28.9998, 13.5996)), (L, (28.9998, 22.1993)),
        (L, (45.9998, 22.1993)), (L, (45.9998, 13.5996)), (L, (50.9682, 18.8374)), (L, (50.9682, 30.0122))])),
    # the corner gussets' inner faces run at 45 deg in plan: x 29 -> 25 (and 46 -> 50) from YP to YF
    dict(name="Gusset taper L", op="cut", axis="z", lo=13.5996, hi=22.1993, loop=((28.9998, YP), [
        (L, (24.9998, YF)), (L, (28.9998, YF)), (L, (28.9998, YP))])),
    dict(name="Gusset taper R", op="cut", axis="z", lo=13.5996, hi=22.1993, loop=((45.9998, YP), [
        (L, (45.9998, YF)), (L, (49.9998, YF)), (L, (45.9998, YP))])),
    dict(name="Arm L", op="join", axis="x", lo=XL, hi=TL, loop=((YB, 5.0), [
        (L, (0.0, 5.0)), (A, (0.0, 0.0), (0.0, -5.0), -1), (L, (YB, -5.0)), (L, (YB, 5.0))])),
    dict(name="Arm R", op="join", axis="x", lo=TR, hi=XR, loop=((YB, 5.0), [
        (L, (10.47, 5.0)), (A, (10.47, 0.0), (10.47, -5.0), -1), (L, (YB, -5.0)), (L, (YB, 5.0))])),
    dict(name="Arm L chamfer", op="chamfer", d=1.0, face=("x", TL), skip=("y", YP),
         csg=chamfer_csg(TL, +1, 0.0)),
    dict(name="Arm R chamfer", op="chamfer", d=1.0, face=("x", TR), skip=("y", YP),
         csg=chamfer_csg(TR, -1, 10.47)),
    dict(name="Arm root L", op="join", axis="z", lo=-5.0, hi=5.0, loop=((27.4588, YP), [
        (L, (25.4588, YP + 2.0)), (L, (25.4588, YP)), (L, (27.4588, YP))])),
    dict(name="Arm root R", op="join", axis="z", lo=-5.0, hi=5.0, loop=((47.5407, YP), [
        (L, (49.5407, YP)), (L, (49.5407, YP + 2.0)), (L, (47.5407, YP))])),
    dict(name="Pivot hole L", op="cut", axis="x", lo=XL, hi=TL, circle=((0.0, 0.0), 2.0)),
    dict(name="Pivot hole R", op="cut", axis="x", lo=TR, hi=XR, circle=((0.0, 0.0), 2.0)),
    dict(name="End hole R", op="cut", axis="x", lo=TR, hi=XR, circle=((10.47, 0.0), 1.5)),
    dict(name="Window", op="cut", axis="y", lo=YB, hi=YP, loop=((43.9998, -5.2507), [
        (L, (43.9998, 15.5493)), (A, (42.7498, 15.5493), (42.7498, 16.7993), 1), (L, (32.2498, 16.7993)),
        (A, (32.2498, 15.5493), (30.9998, 15.5493), 1), (L, (30.9998, -5.2507)),
        (A, (32.2498, -5.2507), (32.2498, -6.5007), 1), (L, (35.3266, -6.5007)), (L, (35.3266, -8.6007)),
        (L, (36.5111, -8.6007)), (A, (37.4998, -8.7507), (38.4885, -8.6007), 1), (L, (39.673, -8.6007)),
        (L, (39.673, -6.5007)), (L, (42.7498, -6.5007)), (A, (42.7498, -5.2507), (43.9998, -5.2507), 1)])),
    dict(name="Top hole L", op="cut", axis="y", lo=YB, hi=YF, circle=((27.4936, 26.1058), 1.5)),
    dict(name="Top hole R", op="cut", axis="y", lo=YB, hi=YF, circle=((47.5059, 26.1058), 1.5)),
    dict(name="Centre hole", op="cut", axis="y", lo=YB, hi=YP, circle=((37.4998, 19.0493), 1.0)),
]
