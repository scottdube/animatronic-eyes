# Servo Block as axis-aligned extrusions, in the STL's frame. Decoded 2026-10-13 with tools/meshcad (levels;
# secplot in x, y and z; profile2d on the y = -21.173 / -16.773 / 6.527 / 10.927, x = 2.115 / 17.915 and
# z = 63.743 / 65.743 caps; verts.py for the hole lengths); checked with tools/meshcad/xcsg.py.
# A 5 mm top plate over two 4.4 mm walls (back and front) that carry the servo pockets, the front face raked
# back 2 in 12; feet on the back outer columns for the Main Base posts; a recessed Nilheim logo on top.
# Symmetric about x = 37.5 in the walls; values are the mesh's.
import json, os

STL = "../../kit-stl/Servo Block.stl"
TITLE = "Servo Block native"
DESCRIPTION = "Native rebuild of the kit's Servo Block (hardware/native/specs/servo_block.py via spec_native.py)"

X0, X1 = 2.1152, 72.8848          # end faces
YB, YBI = -21.1733, -16.7733      # back wall back / inner face
YFI, YF = 6.5267, 10.9267         # front wall inner / front face
YT = 8.9267                       # top front edge; the front face rakes from here to (YF, ZR)
ZR = 53.7428                      # where the rake meets the vertical front face
ZP, ZT = 60.7428, 65.7428         # plate underside and top
L, A = "L", "A"


def wall(lo_z_outer, mid_z):
    """Wall loop in (x, z), top at ZT (it overlaps the plate). The outer columns go down to lo_z_outer,
    the wide pocket's lintel to mid_z; 3 mm 45-degree gussets under the plate, a 3 mm chamfer in the narrow
    pocket."""
    return ((X0, ZT), [
        (L, (X0, lo_z_outer)), (L, (10.1152, lo_z_outer)), (L, (10.1152, 57.7428)), (L, (13.1152, ZP)),
        (L, (14.9152, ZP)), (L, (17.9152, 57.7428)), (L, (17.9152, 47.7592)), (L, (22.6508, 47.7592)),
        (L, (25.6508, 44.7592)), (L, (25.6508, 34.0592)), (L, (33.6508, 34.0592)), (L, (33.6508, mid_z)),
        (L, (57.0848, mid_z))] + ([(L, (57.0848, 57.7428))] if mid_z != 57.7428 else []) + [  # no zero-length line
        (L, (60.0848, ZP)), (L, (61.8848, ZP)), (L, (64.8848, 57.7428)), (L, (64.8848, lo_z_outer)), (L, (X1, lo_z_outer)), (L, (X1, ZT)), (L, (X0, ZT))])


def foot(name, xa, xb):
    """Back foot under an outer column: 2 mm proud of the back wall's inner face, 4 mm tall, then a slope
    up to the inner face at z 35.1038."""
    return dict(name=name, op="join", axis="x", lo=xa, hi=xb, loop=((YBI - 0.5, 28.0592), [
        (L, (-14.7733, 28.0592)), (L, (-14.7733, 32.0592)), (L, (YBI, 35.1038)), (L, (YBI - 0.5, 35.1038)),
        (L, (YBI - 0.5, 28.0592))]))


# The logo is traced, not designed here: its outlines are the mesh's own vertices (caploops.py at z 65.743),
# drawn as fitted splines between corners with every fit point fixed, so the sketch is fully constrained
# without a dimension on each of ~290 points. Edit it as artwork, not by dimension.
_LOGO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profiles",
                                    "servo_block_logo.json")))["loops"]
LOGO_C, LOGO_R = (37.6833, -6.5179), 10.7908      # recess floor circle; the 1 mm rim chamfer makes R11.7908 on top
ZL = 63.7428                                      # recess floor

FEATURES = [
    dict(name="Plate", op="new", axis="x", lo=X0, hi=X1, loop=((YB, ZP), [
        (L, (YF, ZP)), (L, (YF, ZT)), (L, (YB, ZT)), (L, (YB, ZP))])),
    dict(name="Back wall", op="join", axis="y", lo=YB, hi=YBI, loop=wall(28.0592, 47.7592)),
    dict(name="Front wall", op="join", axis="y", lo=YFI, hi=YF, loop=wall(34.0592, 57.7428)),
    dict(name="Front rake", op="cut", axis="x", lo=X0 - 1, hi=X1 + 1, loop=((YT, ZT), [
        (L, (YF, ZR)), (L, (YF + 0.5, ZR)), (L, (YF + 0.5, ZT + 0.5)), (L, (YT, ZT + 0.5)), (L, (YT, ZT))])),
    foot("Foot L", X0, 10.1152),
    foot("Foot R", 64.8848, X1),
    # R1 rod holes straight through, front and back, at two heights
    dict(name="Rod hole back low", op="cut", axis="x", lo=X0 - 0.5, hi=X1 + 0.5, circle=((-19.0233, 41.2428), 1.0)),
    dict(name="Rod hole back high", op="cut", axis="x", lo=X0 - 0.5, hi=X1 + 0.5, circle=((-19.0233, 54.2428), 1.0)),
    dict(name="Rod hole front low", op="cut", axis="x", lo=X0 - 0.5, hi=X1 + 0.5, circle=((8.7767, 41.2428), 1.0)),
    dict(name="Rod hole front high", op="cut", axis="x", lo=X0 - 0.5, hi=X1 + 0.5, circle=((8.7767, 54.2428), 1.0)),
    # Ø3 screw holes from each end into the Main Base posts: 10 mm blind in the plate, through the feet (cuts run 0.5 mm past a face: see TRAPS)
    dict(name="Screw hole top L", op="cut", axis="x", lo=X0 - 0.5, hi=12.1152, circle=((-18.7303, 62.9667), 1.5)),
    dict(name="Screw hole top R", op="cut", axis="x", lo=62.8848, hi=X1 + 0.5, circle=((-18.7303, 62.9667), 1.5)),
    dict(name="Screw hole foot L", op="cut", axis="x", lo=X0 - 0.5, hi=10.6152, circle=((-17.9733, 30.943), 1.5)),
    dict(name="Screw hole foot R", op="cut", axis="x", lo=64.3848, hi=X1 + 0.5, circle=((-17.9733, 30.943), 1.5)),
    dict(name="Logo recess", op="cut", axis="z", lo=ZL, hi=ZT + 0.5, circle=(LOGO_C, LOGO_R)),
    dict(name="Logo rim chamfer", op="chamfer", d=1.0, pick=[(LOGO_C[0] + LOGO_R, LOGO_C[1], ZT)],
         csg=[dict(name="rim cone", op="cut", axis="z", lo=0, hi=0, revolve=dict(
             centre=LOGO_C, pts=[(0.0, ZT - 1.0), (LOGO_R, ZT - 1.0), (LOGO_R + 1.5, ZT + 0.5), (0.0, ZT + 0.5)],
             a0=0.0, a1=360.0))]),
] + [dict(name="Logo %d" % (k + 1), op="join", axis="z", lo=ZL - 0.5, hi=ZT, runs=runs)
     for k, runs in enumerate(_LOGO)]
