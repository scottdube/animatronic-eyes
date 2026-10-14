# Bottom Left Lid, decoded 2026-10-13 with tools/meshcad on the STL turned -18.47655 deg about x (rotstl.py), the
# lip frame, and -20 deg, the shell frame (planes.py; profile2d on the z' = 4 / -0.409 caps; section2d at x 0 and
# z' 3..-8; circle fits per frame; the bore's triangles read one by one). FRAME turns the body back to the STL's.
# Unlike the top lids it is drawn in TWO frames: the shell and an inner ring ("ring A") sit at 20 deg like the top
# lid's, the lip ring ("ring B"), ears and tab at 18.47655 deg. The union shows it: the bore is ring B's vertical
# wall above z' ~2.06 and ring A's wall (tilted 1.52 deg) below it, and ring A's underside shows below ring B for
# |x| < 10.92. So the shell frame is built first, turned 1.52345 deg into the lip frame (a rotate op), then the rest.
# Values are the mesh's.
import math

STL = "../../kit-stl/Bottom Left Lid.stl"
TITLE = "Bottom Left Lid native"
DESCRIPTION = "Native rebuild of the kit's Bottom Left Lid (hardware/native/specs/bottom_left_lid.py via spec_native.py)"
FRAME = ("x", 18.47655)           # lip frame; STL = Rx(18.47655) * drawing (lip-plane normal fit)
TILT = 20.0 - FRAME[1]            # shell frame -> lip frame

# shell frame
C = (0.0, -0.093969)              # shell centre (x, y'') = STL (0, -0.1, 0) turned 20 deg
Z0 = 0.034202                     # shell equator = ring A underside
RO, RI = 18.435, 16.5             # shell outer / inner sphere (same as the top lids)
RA = 19.8423                      # ring A outside, about C (fit on the equator flat's vertices, resid 0.00001)
ZA = 3.0                          # ring A top: a choice, hidden inside ring B (B's wall takes over at z' ~2.2)
ZE = Z0 + 0.5                     # the shell runs 0.5 up into ring A so the join overlaps (see TRAPS)
# lip frame
ZB0, ZT = -0.409, 4.0             # ring B underside / top; the ears' R4 is tangent to the top
RB = 20.102                       # ring B outside, about the pivot axis (the origin)
CB, RBI = (0.0, -0.1528), 16.502  # ring B bore, vertical in this frame (fit at z' 4, resid 0.0007)
YP = -3.8068                      # ring B is cut back to y' YP above where the R4.5 pivot clearance meets it
XE0, XE1 = 18.2, 19.7             # ear inner / outer face
S, CO = math.sin(math.radians(FRAME[1])), math.cos(math.radians(FRAME[1]))
YC, TN = -0.1 / CO, S / CO        # STL y = -0.1 in (y', z'): y' = YC + TN z'
L, A = "L", "A"


def sector(c, r0, r1, a0, a1):
    """Annular sector about c, radii r0..r1, angles a0..a1 deg counter-clockwise, as a loop."""
    pt = lambda r, a: (c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a)))
    return (pt(r0, a0), [(L, pt(r1, a0)), (A, c, pt(r1, a1), 1), (L, pt(r0, a1)), (A, c, pt(r0, a0), -1)])


def ear(name, x0, x1):
    """R4 about the pivot, squared off toward the ring: the quarter y' -4..0, z' ZB0..ZT is filled (profile2d on
    the x 19.7 cap), which is what joins the ear to the ring past the R4.5 clearance."""
    yb = -(4.0 ** 2 - ZB0 ** 2) ** 0.5
    return dict(name=name, op="join", axis="x", lo=x0, hi=x1, loop=((-4.0, ZT), [
        (L, (-4.0, ZB0)), (L, (yb, ZB0)), (A, (0.0, 0.0), (0.0, ZT), 1), (L, (-4.0, ZT))]))


def ear_hole(name, x0, x1):
    return dict(name=name, op="cut", axis="x", lo=x0, hi=x1, circle=((0.0, 0.0), 1.75))


_ZC = (4.5 ** 2 - YP ** 2) ** 0.5                                   # 2.3997: R4.5 meets y' = YP


def clearance(name, x0, x1):
    """Cut from x0 to x1: R4.5 about the pivot, y' > YP above where that circle meets it, and y' > 0 at every
    height (nothing of the lid is there)."""
    return dict(name=name, op="cut", axis="x", lo=x0, hi=x1, loop=((YP, _ZC), [
        (L, (YP, ZT + 0.5)), (L, (21.0, ZT + 0.5)), (L, (21.0, -21.0)), (L, (0.0, -21.0)), (L, (0.0, -4.5)),
        (A, (0.0, 0.0), (YP, _ZC), -1)]))
_XB = (RB ** 2 - CB[1] ** 2) ** 0.5                                 # ring B outside at y' = CB's

FEATURES = [
    # --- shell frame
    dict(name="Ring A", op="new", axis="z", lo=Z0, hi=ZA, loop=sector(C, RI, RA, 180.0, 360.0)),
    dict(name="Shell", op="join", axis="z", lo=0, hi=0, revolve=dict(centre=C, loop=((RI, ZE), [
        (L, (RO, ZE)), (L, (RO, Z0)), (A, (0.0, Z0), (0.0, Z0 - RO), -1), (L, (0.0, Z0 - RI)),
        (A, (0.0, Z0), (RI, Z0), 1), (L, (RI, ZE))]))),
    dict(name="Shell to lip frame", op="rotate", axis="x", deg=TILT),
    # --- lip frame
    dict(name="Ring B", op="join", axis="z", lo=ZB0, hi=ZT, loop=((RBI, CB[1]), [
        (L, (_XB, CB[1])), (A, (0.0, 0.0), (-_XB, CB[1]), -1), (L, (-RBI, CB[1])), (A, CB, (RBI, CB[1]), 1)])),
    # STL plane y = -0.1 trims the shell (inside the pivot clearance it also clips the rings' ends)
    dict(name="Shell trim y-0.1", op="cut", axis="x", lo=-21.0, hi=21.0, loop=((YC - 25.0 * TN, -25.0), [
        (L, (YC + 25.0 * TN, 25.0)), (L, (30.0, 25.0)), (L, (30.0, -25.0)), (L, (YC - 25.0 * TN, -25.0))])),
    # R4.5 clearance about the pivot between the ears, the rings cut back to y' YP above it; past the ears' outer
    # faces the same region goes (the ring outside meets x 19.7 at y' -4.0). Under the ears the ring stays solid
    # out to the ear (section2d at x 19 / 18.5).
    clearance("Pivot clearance", -XE0, XE0),
    clearance("Past ear R", XE1, 21.0),
    clearance("Past ear L", -21.0, -XE1),
    ear("Ear R", XE0, XE1),
    ear("Ear L", -XE1, -XE0),
    ear_hole("Ear hole R", XE0 - 0.5, XE1 + 0.5),
    ear_hole("Ear hole L", -XE1 - 0.5, -XE0 + 0.5),
    # link tab off the ring at the left ear's side, 45-degree corner; the ring is notched square beside it
    dict(name="Tab notch", op="cut", axis="z", lo=ZB0 - 0.5, hi=ZT + 0.5, loop=((-14.1348, -13.2933), [
        (L, (-14.1348, -21.0)), (L, (-21.0, -21.0)), (L, (-21.0, -13.2933)), (L, (-14.1348, -13.2933))])),
    dict(name="Tab", op="join", axis="z", lo=ZB0, hi=ZT, loop=((-14.1348, -13.2933), [
        (L, (-6.0, -18.5)), (L, (-13.1348, -18.5)), (L, (-14.1348, -17.5)), (L, (-14.1348, -13.2933))])),
    dict(name="Tab pin hole", op="cut", axis="x", lo=-14.1348 - 0.5, hi=-8.1348,
         circle=((-16.0, (ZB0 + ZT) / 2), 1.0)),
]
