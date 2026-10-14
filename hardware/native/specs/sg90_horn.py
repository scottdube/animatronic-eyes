# SG90 double-arm horn, decoded 2026-10-14 from the kit's Complete Model.stl (the tilt servo's horn, extracted to
# hardware/kit-stl/from-complete-model/ in its servo's frame and turned 0.2333 deg so its arms lie on Y). Same frame as
# specs/sg90.py: Z up the shaft, origin on the shaft axis at the servo's case top, so a horn occurrence is its servo's
# transform turned about Z. Hub z 5.45 (sits 2.0 down the spline) to the arm plate, arm plate 7.85..9.25.
# SIMPLIFIED: the spline socket is a plain R2.45 bore to match the servo's plain spline (the mesh's teeth run
# r 2.38..2.55), and the hub's blend into the arms (R9..R47 facets at z 6.5) is the R3.45 circle it approximates.
import math

STL = "../../kit-stl/from-complete-model/SG90 Horn.stl"
TITLE = "SG90 Horn native"
DESCRIPTION = "SG90 double-arm horn, simplified, decoded from the kit's Complete Model (hardware/native/specs/sg90_horn.py)"
GATE_MM = 0.11      # the socket's teeth against the plain bore
L, A = "L", "A"

Z0, ZP, Z1 = 5.45, 7.85, 9.25    # hub bottom, arm plate underside, top
RHUB = 3.45
HX, HY = 2.65, 2.2091            # where each arm's straight side leaves the hub circle (on R3.45)
YE, RE = 14.05, 2.0              # arm end arcs
HOLES = (4.45, 6.45, 8.45, 10.45, 12.45, 14.45)   # Ø1.2 on both arms, 2 mm pitch
RHOLE = 0.6
RSOCK, ZSOCK = 2.45, 7.45        # spline socket (the shaft's top is at 7.45)
RSCREW, RCB, ZCB = 1.05, 2.3, 8.25   # screw hole, and the counterbore for its head from 8.25 up


def _tangent():
    """the point where the line from (HX, HY) touches the end circle on its outside (x > 0)"""
    dx, dy = 0.0 - HX, YE - HY
    d = math.hypot(dx, dy)
    a = math.atan2(dy, dx) - math.asin(RE / d)   # direction to the tangent point, turned toward +x
    t = math.sqrt(d * d - RE * RE)
    return HX + t * math.cos(a), HY + t * math.sin(a)


TX, TY = _tangent()
PLATE = ((-HX, -HY), [(L, (-TX, -TY)), (A, (0.0, -YE), (TX, -TY), 1), (L, (HX, -HY)),
                      (A, (0.0, 0.0), (HX, HY), 1), (L, (TX, TY)), (A, (0.0, YE), (-TX, TY), 1),
                      (L, (-HX, HY)), (A, (0.0, 0.0), (-HX, -HY), 1)])

FEATURES = [
    dict(name="Hub", op="new", axis="z", lo=Z0, hi=ZP, circle=((0.0, 0.0), RHUB)),
    dict(name="Arms", op="join", axis="z", lo=ZP, hi=Z1, loop=PLATE),
    dict(name="Spline socket", op="cut", axis="z", lo=Z0 - 0.5, hi=ZSOCK, circle=((0.0, 0.0), RSOCK)),
    dict(name="Screw hole", op="cut", axis="z", lo=ZSOCK - 0.5, hi=Z1 + 0.5, circle=((0.0, 0.0), RSCREW)),
    dict(name="Counterbore", op="cut", axis="z", lo=ZCB, hi=Z1 + 0.5, circle=((0.0, 0.0), RCB)),
] + [dict(name="Hole %+g" % (s * y), op="cut", axis="z", lo=ZP - 0.5, hi=Z1 + 0.5, circle=((0.0, s * y), RHOLE))
     for y in HOLES for s in (1, -1)]
