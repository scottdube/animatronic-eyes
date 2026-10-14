# SG90 micro servo, decoded 2026-10-14 from the six servos inside the kit's Complete Model.stl (the tilt servo's copy,
# extracted by hardware/kit-stl/from-complete-model/: lower case, tab section, two labels, four case screws and the
# cable stub). Servo frame: Z up the output shaft, origin on the shaft axis at the top face of the case, +Y from the
# case's centre toward the shaft (the shaft sits 6.1 from the front end, 16.4 from the back).
# A bought part, so this is SIMPLIFIED where the mesh is detail nobody fits to: the spline is a plain R2.45 cylinder
# (the mesh's teeth run r 2.35..2.5), the gear tower's 0.1 top round and base fillet are square, and the labels
# (0.1 stickers) are left off. Everything that locates the servo is the mesh's to 0.0001: case, tabs, tab holes and
# slots, shaft position and height, cable stub.
STL = "../../kit-stl/from-complete-model/SG90.stl"
TITLE = "SG90 native"
DESCRIPTION = "SG90 micro servo, simplified, decoded from the kit's Complete Model (hardware/native/specs/sg90.py)"
GATE_MM = 0.11      # the spline teeth (r 2.5 peaks vs the R2.45 cylinder) and the tower's 0.1 round; see EXEMPT
L, A = "L", "A"

W = 6.1                    # half width of the case and tabs
Y0, Y1 = -16.4, 6.1        # case, back to front
T0, T1 = -21.2, 10.9       # tabs
ZB, ZT0, ZT1 = -22.5, -6.7, -4.2   # case bottom, tab plate underside and top
RC = 0.85                  # vertical corner rounds of case and tabs
HOLE_R, SLOT = 1.1, 0.55   # Ø2.2 tab holes, 1.1 wide slot out to the tab end
YH = (-19.05, 8.75)        # tab hole centres: 27.8 apart
ZTW = 4.35                 # gear tower top
RT, RB, YB = 6.1, 2.8, -5.6   # tower: R6.1 about the shaft, R2.8 boss at y -5.6
RS, ZS, CH = 2.45, 7.45, 0.2  # spline radius, shaft top, top chamfer
RH = 0.8                   # Ø1.6 horn screw hole, down to z 0.1
_hy = (HOLE_R ** 2 - SLOT ** 2) ** 0.5


def rrect(x, y0, y1, r):
    """rectangle |u| <= x, y0..y1 with corner rounds r, counter-clockwise from the bottom right"""
    return ((x, y0 + r), [(L, (x, y1 - r)), (A, (x - r, y1 - r), (x - r, y1), 1), (L, (-x + r, y1)),
                          (A, (-x + r, y1 - r), (-x, y1 - r), 1), (L, (-x, y0 + r)),
                          (A, (-x + r, y0 + r), (-x + r, y0), 1), (L, (x - r, y0)),
                          (A, (x - r, y0 + r), (x, y0 + r), 1)])


def keyhole(yh, out):
    """tab hole plus its slot out to the tab end; `out` is the side the slot runs (-1 back, +1 front)"""
    e = yh + out * 2.5                       # past the tab end
    a, b = (SLOT, -SLOT) if out < 0 else (-SLOT, SLOT)
    return ((a, e), [(L, (a, yh + out * _hy)), (A, (0.0, yh), (b, yh + out * _hy), 1), (L, (b, e)), (L, (a, e))])


FEATURES = [
    dict(name="Case", op="new", axis="z", lo=ZB, hi=0.0, loop=rrect(W, Y0, Y1, RC)),
    dict(name="Tabs", op="join", axis="z", lo=ZT0, hi=ZT1, loop=rrect(W, T0, T1, RC)),
    dict(name="Back tab hole", op="cut", axis="z", lo=ZT0 - 0.5, hi=ZT1 + 0.5, loop=keyhole(YH[0], -1)),
    dict(name="Front tab hole", op="cut", axis="z", lo=ZT0 - 0.5, hi=ZT1 + 0.5, loop=keyhole(YH[1], 1)),
    dict(name="Tower", op="join", axis="z", lo=0.0, hi=ZTW, circle=((0.0, 0.0), RT)),
    dict(name="Tower boss", op="join", axis="z", lo=0.0, hi=ZTW, circle=((0.0, YB), RB)),
    dict(name="Shaft", op="join", axis="z", lo=0, hi=0, revolve=dict(centre=(0.0, 0.0), loop=((0.0, ZTW), [
        (L, (RS, ZTW)), (L, (RS, ZS - CH)), (L, (RS - CH, ZS)), (L, (0.0, ZS)), (L, (0.0, ZTW))]))),
    dict(name="Horn screw hole", op="cut", axis="z", lo=0.1, hi=ZS + 0.5, circle=((0.0, 0.0), RH)),
    # the three-wire ribbon leaving the front end: a 3 x 1 stadium in (x, z), 1 out of the case
    dict(name="Cable stub", op="join", axis="y", lo=4.1, hi=7.1, loop=((-1.0, -18.0), [
        (L, (1.0, -18.0)), (A, (1.0, -17.5), (1.0, -17.0), 1), (L, (-1.0, -17.0)), (A, (-1.0, -17.5), (-1.0, -18.0), 1)])),
]

EXEMPT = [
    dict(box=((-6.21, -13.66, -18.71), (-6.09, 3.36, -5.69)), why="label sticker, 0.1 proud of the -X side"),
    dict(box=((6.09, -13.66, -18.71), (6.21, 3.36, -5.69)), why="label sticker, 0.1 proud of the +X side"),
    dict(box=((-2.6, -2.6, 0.05), (2.6, 2.6, 4.3)), why="the shaft mesh runs on inside the tower (internal faces)"),
]
