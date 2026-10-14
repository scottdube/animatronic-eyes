# PlaceHolder Eye (x2), decoded 2026-10-13 with tools/meshcad (section2d at x 0 and z 7.4..-7; vertex rings fitted per
# height; the outer surface least-squares fitted in a tilted frame, resid 8e-7 mm). Axis Z, back face z 7.5, front
# pole z -16.
# It is the eyeball (docs/eyeball-cad.md: R15 sphere, Ø24 bore, Ø1.25 keying rib, three snap recesses) inside a 1 mm
# thicker R16 outer shell, and the STL keeps two quirks of how that shell was made, both reproduced here:
#  - the shell is tilted 0.0278226 deg about +Y (its back plane and every tessellation ring are square to the tilted
#    axis, not to Z) and its back plane sits at 7.493136 there, so the eyeball's own back face (z 7.5, out to its R15
#    sphere at r 12.990381) stands proud of it by 0.0001..0.0125 mm;
#  - each ring of the shell is a circle of radius 0.0087408 + sqrt(16^2 - w^2) about an axis 0.0087408 off centre in
#    +x: an R16 arc centred 0.0087408 out from the revolve axis, not a sphere (a sphere fit leaves 0.0007 mm, this 8e-7).
# Everything else is square to Z through the origin. Values are the mesh's.
import math

STL = "../../kit-stl/PlaceHolder Eye (x2).stl"
TITLE = "PlaceHolder Eye native"
DESCRIPTION = "Native rebuild of the kit's PlaceHolder Eye (hardware/native/specs/placeholder_eye.py via spec_native.py)"
L, A = "L", "A"

TILT = 0.0278226                  # deg about +Y, shell frame -> STL frame
D = 0.0087408                     # shell revolve axis offset in +x (shell frame), = the arc centre's radial offset
RS = 16.0                         # shell arc radius
ZS = 7.493136                     # shell back plane, shell frame
RE = 15.0                         # eyeball sphere; only its back rim shows (r 12.990381 at z 7.5)
ZB = 7.5                          # back face
RB = math.sqrt(RE ** 2 - ZB ** 2) - 1.0   # bore 11.990381: the rim less 1 (the mesh's value is exactly this)
ZC = -7.1                         # bore ceiling
RR, ZR = 0.625, 0.676             # keying rib: half-round R0.625 on the bore wall at -X, from the back face to z ZR
RX = RB + 0.8                     # snap recess wall 12.790381
ZF, ZW, ZP = 0.67551, -1.2, -6.670979   # recess floor (back side), wall end, ramp end
RP = 12.037773                    # the ramp stops here, short of the bore: a 0.047 ledge at ZP closes the recess

_wf = math.sqrt(RS ** 2 - D ** 2)          # where the shell arc meets its axis (front pole)
_rs = D + math.sqrt(RS ** 2 - ZS ** 2)     # shell outside at its back plane


def recess(name, a0, a1):
    """Snap recess: out to RX between the floor ZF and ZW, a straight ramp in to RP at ZP, a flat ledge to the bore. From
    r 11.5 (inside the bore, nothing there) so the cut starts in empty space."""
    return dict(name=name, op="cut", axis="z", lo=0, hi=0, revolve=dict(centre=(0.0, 0.0), a0=a0, a1=a1, loop=(
        (11.5, ZF), [(L, (RX, ZF)), (L, (RX, ZW)), (L, (RP, ZP)), (L, (11.5, ZP)), (L, (11.5, ZF))])))


FEATURES = [
    # --- shell frame
    dict(name="Shell", op="new", axis="z", lo=0, hi=0, revolve=dict(centre=(D, 0.0), loop=((0.0, ZS), [
        (L, (_rs, ZS)), (A, (D, 0.0), (0.0, -_wf), -1), (L, (0.0, ZS))]))),
    dict(name="Shell to STL frame", op="rotate", axis="y", deg=TILT),
    # --- STL frame
    dict(name="Eyeball", op="join", axis="z", lo=0, hi=0, revolve=dict(centre=(0.0, 0.0), loop=((0.0, 0.0), [
        (L, (RE, 0.0)), (A, (0.0, 0.0), (math.sqrt(RE ** 2 - ZB ** 2), ZB), 1), (L, (0.0, ZB)), (L, (0.0, 0.0))]))),
    dict(name="Bore", op="cut", axis="z", lo=ZC, hi=ZB + 0.5, circle=((0.0, 0.0), RB)),
    # half-round facing the axis; its back half runs 0.5 into the wall so the join overlaps (see TRAPS)
    dict(name="Keying rib", op="join", axis="z", lo=ZR, hi=ZB, loop=((-(RB - RR), -RR), [
        (A, (-(RB - RR), 0.0), (-(RB - RR), RR), 1), (L, (-(RB + 0.5), RR)), (L, (-(RB + 0.5), -RR)),
        (L, (-(RB - RR), -RR))])),
    recess("Recess 40", 19.0, 61.0),
    recess("Recess -40", -61.0, -19.0),
    recess("Recess 180", 134.0, 226.0),
]
