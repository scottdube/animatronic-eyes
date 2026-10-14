# Top Left Lid, decoded 2026-10-13 with tools/meshcad on the STL turned +20 deg about x (rotstl.py): in that frame
# the lip's planes are axis-aligned (planes.py; profile2d on the x = +-18 / -8.1348 and z' = 4 / 0.034 caps;
# section2d at z' 2; ringr-style vertex radii). FRAME turns the body back to the STL's frame.
# A spherical shell (centre STL (0, 0.1, 0)) below its equator, a 4 mm lip ring above it about the pivot axis,
# two pivot ears with R1.75 holes, and a link tab with a blind R1 pin hole. Values are the mesh's.
import math

STL = "../../kit-stl/Top Left Lid.stl"
TITLE = "Top Left Lid native"
DESCRIPTION = "Native rebuild of the kit's Top Left Lid (hardware/native/specs/top_left_lid.py via spec_native.py)"
FRAME = ("x", -20.0)              # drawn with the lip planes level; STL = Rx(-20) * drawing

C = (0.0, 0.093969)               # shell centre (x, y') = STL (0, 0.1, 0) turned 20 deg
Z0 = 0.034202                     # shell equator = lip ring underside (z' of that centre)
ZT = 4.0                          # lip ring top; the ears' R4 is tangent to it
RO, RI = 18.435, 16.5             # shell outer / inner sphere
RL = 19.858                       # lip ring outside, about the pivot axis (the origin)
XE0, XE1 = 16.5, 18.0             # ear inner / outer face
L, A = "L", "A"
YC, TN = 0.1 / 0.939693, 0.363970  # STL y = 0.1 in (y', z'): y' = YC - TN z'
ZE = Z0 + 0.5                     # the shell runs 0.5 up into the ring so the join overlaps (see TRAPS)


def sector(c, r0, r1, a0, a1):
    """Annular sector about c, radii r0..r1, angles a0..a1 deg counter-clockwise, as a loop."""
    pt = lambda r, a: (c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a)))
    return (pt(r0, a0), [(L, pt(r1, a0)), (A, c, pt(r1, a1), 1), (L, pt(r0, a1)), (A, c, pt(r0, a0), -1)])


def ear(name, x0, x1):
    return dict(name=name, op="join", axis="x", lo=x0, hi=x1, circle=((0.0, 0.0), 4.0))


def ear_hole(name, x0, x1):
    return dict(name=name, op="cut", axis="x", lo=x0, hi=x1, circle=((0.0, 0.0), 1.75))


def past_ear(name, x0, x1):
    """Beyond the ears the ring is cut back to R4.5 about the pivot, and to y' 2.8 where that circle runs
    under the ring top."""
    zc = (4.5 ** 2 - 2.8 ** 2) ** 0.5                               # 3.5228
    return dict(name=name, op="cut", axis="x", lo=x0, hi=x1, loop=((-6.0, -6.0), [
        (L, (2.8, -6.0)), (L, (2.8, -zc)), (A, (0.0, 0.0), (2.8, zc), 1), (L, (2.8, ZT + 0.5)),
        (L, (-6.0, ZT + 0.5)), (L, (-6.0, -6.0))]))


FEATURES = [
    dict(name="Lip ring", op="new", axis="z", lo=Z0, hi=ZT, circle=((0.0, 0.0), RL)),
    # the eye's cavity carries straight up through the ring (same R16.5 and centre as the shell's inside)
    dict(name="Ring bore", op="cut", axis="z", lo=Z0 - 0.5, hi=ZT + 0.5, circle=(C, RI)),
    dict(name="Shell", op="join", axis="z", lo=0, hi=0, revolve=dict(centre=C, loop=((RI, ZE), [
        (L, (RO, ZE)), (L, (RO, Z0)), (A, (0.0, Z0), (0.0, Z0 - RO), -1), (L, (0.0, Z0 - RI)),
        (A, (0.0, Z0), (RI, Z0), 1), (L, (RI, ZE))]))),
    # STL plane y = 0.1 trims the shell; the ring is a half ring, y' >= 0 (any cut between y' 0 and 0.094 is
    # hidden by the ears and the past-ear cuts, so y' 0 is a choice, not a measurement)
    dict(name="Shell trim y0.1", op="cut", axis="x", lo=-21.0, hi=21.0, loop=((YC + 25.0 * TN, -25.0), [
        (L, (YC - 25.0 * TN, 25.0)), (L, (-30.0, 25.0)), (L, (-30.0, -25.0)), (L, (YC + 25.0 * TN, -25.0))])),
    dict(name="Ring half", op="cut", axis="z", lo=Z0 - 0.5, hi=ZT + 0.5, loop=((-21.0, 0.0), [
        (L, (21.0, 0.0)), (L, (21.0, -21.0)), (L, (-21.0, -21.0)), (L, (-21.0, 0.0))])),
    past_ear("Past ear R", XE1, 21.0),
    past_ear("Past ear L", -21.0, -XE1),
    ear("Ear R", XE0, XE1),
    ear("Ear L", -XE1, -XE0),
    ear_hole("Ear hole R", XE0 - 0.5, XE1 + 0.5),
    ear_hole("Ear hole L", -XE1 - 0.5, -XE0 + 0.5),
    # link tab off the ring at the left ear's side, 45-degree corner; the ring is notched square beside it
    dict(name="Tab notch", op="cut", axis="z", lo=Z0 - 0.5, hi=ZT + 0.5, loop=((-14.1348, 13.1481), [
        (L, (-21.0, 13.1481)), (L, (-21.0, 21.0)), (L, (-14.1348, 21.0)), (L, (-14.1348, 13.1481))])),
    dict(name="Tab", op="join", axis="z", lo=Z0, hi=ZT, loop=((-14.1348, 13.1481), [
        (L, (-14.1348, 17.5)), (L, (-13.1348, 18.5)), (L, (-6.0, 18.5)), (L, (-14.1348, 13.1481))])),
    dict(name="Tab pin hole", op="cut", axis="x", lo=-14.1348 - 0.5, hi=-8.1348,
         circle=((16.0, (Z0 + ZT) / 2), 1.0)),
    # R1 pocket along x into the bore wall at the right ear's side (y' 6.982, z' 0.5). Its floor is not flat: it
    # is a cylinder R17.1816 about the bore's own axis (every floor vertex sits there within 0.0001). Built as the
    # R1 cut run 0.4 past the floor, then the floor's outside put back as an annular sector about the bore axis.
    dict(name="Pocket", op="cut", axis="x", lo=13.5, hi=16.5, circle=((6.982, 0.5), 1.0)),
    dict(name="Pocket floor", op="join", axis="z", lo=-0.5, hi=1.5, loop=sector(C, 17.1816, 18.35, 15.0, 32.0)),
]
