# Main Base as axis-aligned extrusions, in the STL's frame. Decoded 2026-10-13 with tools/meshcad (levels, secplot
# along x and y, profile2d on the y caps, raw vertices for the plate's top corners); checked with xcsg.py.
# Near-symmetric about x = 37.5: a 5 mm back plate, four pivot arms on the y = 0, z = 0 axis, gussets on the outer
# arms, an upper block and four servo-tab posts with holes along x.
STL = "../../kit-stl/Main Base.stl"
TITLE = "Main Base native"
DESCRIPTION = "Native rebuild of the kit's Main Base (hardware/native/specs/main_base.py via spec_native.py)"

YB, YP = -28.5322, -23.5322     # back face, plate front
L, A = "L", "A"


def arm(name, x0, x1):
    """Pivot arm: z +-5 from the plate to an R5 end about (y 0, z 0)."""
    return dict(name=name, op="join", axis="x", lo=x0, hi=x1, loop=((YB, 5.0), [
        (L, (0.0, 5.0)), (A, (0.0, 0.0), (0.0, -5.0), -1), (L, (YB, -5.0)), (L, (YB, 5.0))]))


SLOPE = 7.45 / 3.0              # outer gusset top: z = 19.9 at the plate front, 12.45 at y -20.5322, 5 at -17.5322
YG = YP + 14.9 / SLOPE          # -17.5322, where that plane reaches the arm top


def root(name, apex, back, z1, clip=None):
    """45-degree root fill between an arm side and the plate, in plan: apex on the arm side 3 mm in front of the
    plate, carried back along the same plane to y -26.0322 (where it bounds the bottom bevel's end). clip: the x of
    the plate's centre notch edge, where the fill stops short of `back`."""
    (xa, ya), xb = apex, back
    if clip is None:
        segs = [(L, (xb, -26.0322))]
    else:
        segs = [(L, (clip, ya - abs(clip - xa))), (L, (clip, -26.0322))]
    return dict(name=name, op="join", axis="z", lo=-5.0, hi=z1, loop=((xa, ya), segs + [
        (L, (xa, -26.0322)), (L, (xa, ya))]))


def outer_chamfer(name, xo, sgn):
    """1 mm chamfer round an outer arm's outside face: bottom edge from the back face, the R5 end, the top edge from
    where the gusset plane meets z = 5. sgn = +1 for the left arm (outside face toward -x). Fusion: one chamfer on
    the tangent chain picked at the end arc's midpoint; here, two prism cuts and a cone."""
    xi = xo + sgn * 1.0
    xf = xo - sgn * 0.5
    csg = [dict(name="ch bot", op="cut", axis="y", lo=YB, hi=0.0, loop=((xf, -3.5), [
               (L, (xo + sgn * 1.5, -5.5)), (L, (xf, -5.5)), (L, (xf, -3.5))])),
           dict(name="ch top", op="cut", axis="y", lo=YG, hi=0.0, loop=((xf, 3.5), [
               (L, (xf, 5.5)), (L, (xo + sgn * 1.5, 5.5)), (L, (xf, 3.5))])),
           dict(name="ch end", op="cut", axis="x", lo=0, hi=0, revolve=dict(centre=(0.0, 0.0), a0=-90.0, a1=90.0,
               pts=[(3.5, xf), (5.0, xi), (6.0, xi), (6.0, xf)])),
           # the chamfer face stops against the gusset plane, which carries on below z 5 for 0.4 mm
           dict(name="ch stop", op="join", axis="x", lo=min(xo, xi), hi=max(xo, xi), loop=((YG, 5.0), [
               (L, (YG + 1.0 / SLOPE, 4.0)), (L, (YG, 4.0)), (L, (YG, 5.0))]))]
    return dict(name=name, op="chamfer", d=1.0, pick=[(xo, 5.0, 0.0)], csg=csg)


# Upper block: 2 mm proud of the plate between the two post pairs, its bottom chamfered back to z 25 where it hangs
# below the plate's centre notch. Posts (servo tabs, x 3 mm) stand forward of it with a hole along x each; 45-degree
# gussets in plan beside each post pair. The lower posts' and gussets' bottom is a plane tilted 0.2 degrees
# (z 28.0354 at the block face, 28.0592 at the post front): the mesh's, kept.
YF = -21.4733                   # block front face
KB = (28.0592 - 28.0354) / (-14.7733 - YF)
zb = lambda y: 28.0354 + KB * (y - YF)
YC = -23.5                      # block bottom chamfer: (YF, 27) -> (YC, 25), carried on to the plate face
ZC = 27.0 - 2.0 * (YF - YP) / (YF - YC)
M = lambda x: 75.0 - x          # mirror about x = 37.5


def side(n, s):
    """Gussets and posts at one end of the block; s = +1 left (x -3.68 .. 1.82), -1 right (mirrored)."""
    X = (lambda x: x) if s > 0 else M
    lo_hi = lambda a, b: (min(X(a), X(b)), max(X(a), X(b)))
    ug = [(-3.6, 34.7038), (-0.6848, 34.7038), (-0.6848, 68.4823), (-1.1848, 68.4823), (-1.1848, 67.5429),
          (-3.6, 67.5429 - 2.4152 * (67.5429 - 56.8868) / (-1.1848 + 11.1695))]
    ug = [(X(x), z) for x, z in ug]
    if s < 0:
        ug = ug[::-1]
    ucut = [(-3.4348, YP), (-1.1848, -21.2822), (-1.1848, YF), (-0.5, YF), (-0.5, -21.0), (-5.0, -21.0), (-5.0, YP)]
    lcut = [(-3.6848, YP), (-1.1848, -21.0322), (-1.1848, -20.5), (-5.0, -20.5), (-5.0, YP)]
    pl = lambda pts: [(X(x), y) for x, y in (pts if s > 0 else pts[::-1])]
    loop = lambda pts: (pts[0], [(L, q) for q in pts[1:] + pts[:1]])
    lo, hi = lo_hi(-3.7, -0.6848)
    plo, phi = lo_hi(-1.1848, 1.8152)
    return [
        dict(name="Gusset upper " + n, op="join", axis="y", lo=YP - 0.5, hi=-21.2822, loop=loop(ug)),
        dict(name="Gusset lower " + n, op="join", axis="x", lo=lo, hi=hi, loop=loop(
            [(YP - 0.5, zb(YP - 0.5)), (-21.0322, zb(-21.0322)), (-21.0322, 34.7038), (YP - 0.5, 34.7038)])),
        dict(name="Gusset upper taper " + n, op="cut", axis="z", lo=34.7038, hi=69.0, loop=loop(pl(ucut))),
        dict(name="Gusset lower taper " + n, op="cut", axis="z", lo=27.0, hi=34.7038, loop=loop(pl(lcut))),
        dict(name="Post upper " + n, op="join", axis="x", lo=plo, hi=phi, loop=loop(
            [(YF - 0.5, 60.7428), (-14.5294, 60.7428), (-14.5294, 65.9301), (-18.7258, 68.4823), (YF - 0.5, 68.4823)])),
        dict(name="Post lower " + n, op="join", axis="x", lo=plo, hi=phi, loop=loop(
            [(YP - 0.5, zb(YP - 0.5)), (-14.7733, 28.0592), (-14.7733, 32.0592), (-16.5105, 34.7038),
             (YP - 0.5, 34.7038)])),
        dict(name="Post hole upper " + n, op="cut", axis="x", lo=plo - 0.5, hi=phi + 0.5,
             circle=((-18.7303, 62.9667), 1.75)),
        dict(name="Post hole lower " + n, op="cut", axis="x", lo=plo - 0.5, hi=phi + 0.5, circle=((-18.0, 31.0), 1.75)),
    ]


FEATURES = [
    dict(name="Back plate", op="new", axis="y", lo=YB, hi=YP, loop=((-1.1848, 68.4823), [
        (L, (76.1848, 68.4823)), (L, (76.1848, 67.5429)), (L, (86.1695, 56.8868)), (L, (95.0002, 51.0)),
        (L, (95.0002, 20.0)), (L, (98.0002, 5.0)), (L, (98.0002, -4.0)), (L, (97.0002, -5.0)), (L, (47.0, -5.0)),
        (L, (47.0, 6.0382)), (L, (51.8412, 10.8794)), (L, (51.8412, 34.0592)), (L, (23.1588, 34.0592)),
        (L, (23.1588, 10.8794)), (L, (28.0, 6.0382)), (L, (28.0, -5.0)), (L, (-22.0002, -5.0)),
        (L, (-23.0002, -4.0)), (L, (-23.0002, 5.0)), (L, (-20.0002, 20.0)), (L, (-20.0002, 51.0)),
        (L, (-11.1695, 56.8868)), (L, (-1.1848, 67.5429)), (L, (-1.1848, 68.4823))])),
    # 45-degree bevels under the plate's front bottom edge, x -17..17 and 58..92
    dict(name="Bottom bevel L", op="cut", axis="x", lo=-17.0002, hi=16.9998, loop=((-26.0322, -5.0), [
        (L, (YP, -2.5)), (L, (YP + 1.0, -2.5)), (L, (YP + 1.0, -6.0)), (L, (-26.0322, -6.0)), (L, (-26.0322, -5.0))])),
    dict(name="Bottom bevel R", op="cut", axis="x", lo=58.0002, hi=92.0002, loop=((-26.0322, -5.0), [
        (L, (YP, -2.5)), (L, (YP + 1.0, -2.5)), (L, (YP + 1.0, -6.0)), (L, (-26.0322, -6.0)), (L, (-26.0322, -5.0))])),
    arm("Arm outer L", -23.0002, -20.0002),
    arm("Arm inner L", 20.0, 23.1588),
    arm("Arm inner R", 51.8412, 55.0),
    arm("Arm outer R", 95.0002, 98.0002),
    root("Root outer L", (-20.0002, -20.5322), -14.5002, 21.0),
    root("Root inner L-", (20.0, -20.5322), 14.5, 5.0),
    root("Root inner L+", (23.1588, -20.5322), 28.6588, 5.0, clip=28.0),
    root("Root inner R-", (51.8412, -20.5322), 46.3412, 5.0, clip=47.0),
    root("Root inner R+", (55.0, -20.5322), 60.5, 5.0),
    root("Root outer R", (95.0002, -20.5322), 89.5002, 21.0),
    # outer gussets: the plate's slope edge carried forward over the arm, then cut by one plane
    dict(name="Gusset L", op="join", axis="y", lo=YP - 0.5, hi=YG, loop=((-23.0002, 5.0), [
        (L, (-20.0002, 20.0)), (L, (-20.0002, 4.0)), (L, (-23.0002, 4.0)), (L, (-23.0002, 5.0))])),
    dict(name="Gusset R", op="join", axis="y", lo=YP - 0.5, hi=YG, loop=((98.0002, 5.0), [
        (L, (98.0002, 4.0)), (L, (95.0002, 4.0)), (L, (95.0002, 20.0)), (L, (98.0002, 5.0))])),
    dict(name="Gusset plane L", op="cut", axis="x", lo=-24.0, hi=-16.0, loop=((YP, 19.9), [
        (L, (YG, 5.0)), (L, (YG + 1.0, 5.0)), (L, (YG + 1.0, 22.0)), (L, (YP, 22.0)), (L, (YP, 19.9))])),
    dict(name="Gusset plane R", op="cut", axis="x", lo=91.0, hi=99.0, loop=((YP, 19.9), [
        (L, (YG, 5.0)), (L, (YG + 1.0, 5.0)), (L, (YG + 1.0, 22.0)), (L, (YP, 22.0)), (L, (YP, 19.9))])),
    outer_chamfer("Outer chamfer L", -23.0002, +1),
    outer_chamfer("Outer chamfer R", 98.0002, -1),
    dict(name="Block", op="join", axis="y", lo=YP - 0.5, hi=YF, loop=((-1.1848, 68.4823), [
        (L, (76.1848, 68.4823)), (L, (76.1848, 34.7038)), (L, (73.8848, 34.7038)), (L, (73.8848, 24.0)),
        (L, (64.8848, 24.0)), (L, (64.8848, 34.0592)), (L, (10.1152, 34.0592)), (L, (10.1152, 24.0)),
        (L, (-1.1848, 24.0)), (L, (-1.1848, 68.4823))])),
    # the mesh leaves a hairline wedge (0.032 mm at z 25, closing at z 34.06) between this chamfer and the plate:
    # a seam from the source CAD, filled here
    dict(name="Block chamfer L", op="cut", axis="x", lo=-2.0, hi=11.0, loop=((YF, 27.0), [
        (L, (YP, ZC)), (L, (YP, 20.0)), (L, (YF, 20.0)), (L, (YF, 27.0))])),
    dict(name="Block chamfer R", op="cut", axis="x", lo=64.0, hi=74.5, loop=((YF, 27.0), [
        (L, (YP, ZC)), (L, (YP, 20.0)), (L, (YF, 20.0)), (L, (YF, 27.0))])),
    *side("L", +1),
    *side("R", -1),
    dict(name="Pivot holes", op="cut", axis="x", lo=-24.0, hi=99.0, circle=((0.0, 0.0), 1.5)),
    dict(name="Plate hole BL", op="cut", axis="y", lo=YB, hi=YP, circle=((-12.0, 4.0), 1.5)),
    dict(name="Plate hole BR", op="cut", axis="y", lo=YB, hi=YP, circle=((87.0, 4.0), 1.5)),
    dict(name="Plate hole TL", op="cut", axis="y", lo=YB, hi=-21.4733, circle=((9.0, 47.0), 1.5)),
    dict(name="Plate hole TR", op="cut", axis="y", lo=YB, hi=-21.4733, circle=((66.0, 47.0), 1.5)),
]
