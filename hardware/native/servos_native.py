# The six SG90s in "EyeMech assembly": each servo rigid to what it is screwed to, each horn a revolute joint on its
# shaft, and each horn motion-linked to the mechanism joint its coupler drives, so turning a servo moves the eye or lid.
# Run through the Fusion MCP on the open assembly after assembly_native.py (AS_RANGE 20:32 for the servo rows),
# joints_native.py and limits_native.py. Occurrence k of "SG90 native" / "SG90 Horn native" is PCA9685 channel k-1, in
# placements.json's order (tools/meshcad/servo_placements.py).
#   Holders were measured, not assumed (2026-10-14, nearest body): the pan servo sits 0.4 from the Sub Base and 1.7+
#   from everything else, so it tilts with the eyes, which its linkage needs (the Three-Point Connector rides the
#   Forks); the other five sit 0.3 from both the Main Base and the Servo Block.
# Ratios: each coupler closes a four-bar (horn hole -> coupler -> mechanism pin), and a motion link is linear, so the
# ratio is the least-squares slope of the solved four-bar over the mechanism joint's limits; SV_SOLVE prints it and how
# far the linear link strays from the true linkage. RATIOS below holds the values in use. Env:
#   SV_BUILD  1 = rigid groups and the six horn joints
#   SV_SOLVE  1 = solve each four-bar at 9 angles across the mechanism limits, print slope and residual
#   SV_LINK   1 = motion links mechanism -> horn from RATIOS (replacing any), horn limits = mechanism limits / ratio
#   SV_DRIVE  "Servo 2 Top Left Lid=20,..." = set horn joints, print where the mechanism went, how far a real coupler
#             would have to stretch (the linear link's error, mm) and how far the drawn one (counter-rotating, a
#             stand-in) ends from its horn hole, then put every joint back to 0
#   SV_SAVE   1 = save a new version of the assembly
import math, os, sys
import adsk.core, adsk.fusion
sys.path.insert(0, "/Users/scottdube/code/animatronic-eyes/hardware/native")
from joints_native import hole
from limits_native import LIMITS

NAMES = ["Servo 0 Pan", "Servo 1 Tilt", "Servo 2 Top Left Lid", "Servo 3 Bottom Left Lid", "Servo 4 Top Right Lid",
         "Servo 5 Bottom Right Lid"]
# joints_native's two holder groups, remade with the servos in: an occurrence in two rigid groups is legal, but one
# group per holder leaves nothing to wonder about when the solver misbehaves
RIGID = [("Main Base 1 group", ["Main Base native:1", "Servo Block native:1"] +
          ["SG90 native:%d" % k for k in range(2, 7)]),
         ("Sub Base 1 group", ["Sub Base native:1", "Eye Holder native:1", "SG90 native:1"])]
# per servo: mechanism joint, the occurrence that turns with it, its coupler pin (owner, axis, radius, uv as in
# joints_native.JOINTS), the coupler occurrence and its servo-end hole in the coupler's STL frame (mm)
FOURBAR = [
    ("Pan L", "Fork native:1", ("Fork native:1", "Y", 1.5, (0, 14.5)),
     "Three-Point Connector native:1", (37.4998, 6.1, 14.4493)),
    ("Tilt", "Sub Base native:1", ("Sub Base native:1", "X", 1.5, (10.47, 0)),
     "Y-Arm native:1", (1.5, 10.186, 34.0626)),
    ("Top Left Lid", "Top Left Lid native:1", ("Top Left Lid native:1", "X", 1.0, (15.79, 3.278)),
     "Top Lid Link native:1", (-15.435, 13.6053, 36.3006)),
    ("Bottom Left Lid", "Bottom Left Lid native:1", ("Bottom Left Lid native:1", "X", 1.0, (-15.608, 3.951)),
     "Bottom Lid Link native:1", (-15.435, -13.5518, 49.3006)),
    ("Top Right Lid", "Top Right Lid native:1", ("Top Right Lid native:1", "X", 1.0, (15.79, 3.278)),
     "Top Lid Link native:2", (-15.435, 13.6053, 36.3006)),
    ("Bottom Right Lid", "Bottom Right Lid native:1", ("Bottom Right Lid native:1", "X", 1.0, (-15.608, 3.951)),
     "Bottom Lid Link native:2", (-15.435, -13.5518, 49.3006)),
]
HORN_HOLES = (4.45, 6.45, 8.45, 10.45, 12.45, 14.45)
HORN_Z = 8.55            # mid arm plate, horn frame
# mechanism deg per horn deg, SV_SOLVE 2026-10-14, with the worst departure of the linear link from the
# solved four-bar over the mechanism's limits. The sign is Fusion's joint directions, not the hardware's.
RATIOS = {"Servo 0 Pan": 0.99570,                 # 0.049 deg: horn r14.45 against Fork tail r14.5
          "Servo 1 Tilt": 0.98207,                # 1.196 deg, at tilt -32.3: horn r10.45, Y-Arm pin r10.47
          "Servo 2 Top Left Lid": -0.89870,       # 0.434 deg: horn r14.45 against the lid pin at r16.13
          "Servo 3 Bottom Left Lid": -0.90565,    # 0.474 deg
          "Servo 4 Top Right Lid": -0.89876,      # 0.439 deg
          "Servo 5 Bottom Right Lid": -0.90566}   # 0.475 deg


def pt(m, p):
    """mm point p in an occurrence's own frame -> assembly mm, through its transform2 (cm)"""
    q = adsk.core.Point3D.create(*(c / 10 for c in p))
    q.transformBy(m)
    return [q.x * 10, q.y * 10, q.z * 10]


sub = lambda a, b: [x - y for x, y in zip(a, b)]
dot = lambda a, b: sum(x * y for x, y in zip(a, b))
norm = lambda a: math.sqrt(dot(a, a))


def rot(v, k, a):
    """Rodrigues: v turned by a (rad) about unit k"""
    c, s = math.cos(a), math.sin(a)
    kx = [k[1] * v[2] - k[2] * v[1], k[2] * v[0] - k[0] * v[2], k[0] * v[1] - k[1] * v[0]]
    return [v[i] * c + kx[i] * s + k[i] * dot(k, v) * (1 - c) for i in range(3)]


def servo_axis(o):
    a = o.transform2.asArray()
    return [a[3] * 10, a[7] * 10, a[11] * 10], [a[2], a[6], a[10]]      # origin mm, Z


def horn_hole(occ, k, near):
    """the horn hole (assembly mm) nearest `near` across the shaft axis, its radius, and that distance"""
    o, z = servo_axis(occ["SG90 native:%d" % k])
    m = occ["SG90 Horn native:%d" % k].transform2
    best = None
    for h in HORN_HOLES:
        for s in (1, -1):
            q = pt(m, (0, s * h, HORN_Z))
            v = sub(q, near)
            d = math.sqrt(max(0.0, dot(v, v) - dot(v, z) ** 2))
            best = min(best or (d, q, h), (d, q, h))
    return best[1], best[2], best[0]


def run(_context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    occ = {root.occurrences.item(i).name: root.occurrences.item(i) for i in range(root.occurrences.count)}
    J = root.asBuiltJoints
    print(app.activeDocument.name, len(occ), "occurrences,", J.count, "as-built joints")

    if os.environ.get("SV_BUILD"):
        assert not J.itemByName(NAMES[0]), "servo joints already exist"
        for name, names in RIGID:
            root.rigidGroups.itemByName(name).deleteMe()
            c = adsk.core.ObjectCollection.create()
            for n in names:
                c.add(occ[n])
            root.rigidGroups.add(c, False).name = name
        for k, name in enumerate(NAMES, 1):
            s = occ["SG90 native:%d" % k]
            shaft = [f for f in s.bRepBodies.item(0).faces
                     if f.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType
                     and abs(f.geometry.radius * 10 - 2.45) < 0.01]
            assert len(shaft) == 1, "%s: %d R2.45 faces" % (s.name, len(shaft))
            geo = adsk.fusion.JointGeometry.createByNonPlanarFace(shaft[0],
                                                                  adsk.fusion.JointKeyPointTypes.MiddleKeyPoint)
            ji = J.createInput(occ["SG90 Horn native:%d" % k], s, geo)
            ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            J.add(ji).name = name
        print("  %d rigid groups, %d as-built joints" % (root.rigidGroups.count, J.count))

    def setj(values):
        for n, v in values.items():
            J.itemByName(n).jointMotion.rotationValue = math.radians(v)
        adsk.doEvents()

    def home(k):
        """at home: the mechanism pin P0, the horn hole Q0 its coupler reaches, coupler length, closure, hole radius"""
        mech, moving, pin, coupler, end = FOURBAR[k - 1]
        g = hole(occ[pin[0]], *pin[1:])[0].geometry.origin
        P0 = [g.x * 10, g.y * 10, g.z * 10]
        Q0, r, closure = horn_hole(occ, k, pt(occ[coupler].transform2, end))
        return P0, Q0, norm(sub(P0, Q0)), closure, r

    def moved(o, m0, p):
        """p carried by occurrence o's motion since its transform was m0"""
        t = m0.copy()
        t.invert()
        t.transformBy(o.transform2)
        return pt(t, p)

    if os.environ.get("SV_SOLVE"):
        for k, (name, (mech, moving, *_)) in enumerate(zip(NAMES, FOURBAR), 1):
            o, z = servo_axis(occ["SG90 native:%d" % k])
            P0, Q0, L0, closure, r = home(k)
            horn = occ["SG90 Horn native:%d" % k]
            # which way the horn joint turns: +10 on the joint against +10 about the servo's Z
            m0 = horn.transform2.copy()
            setj({name: 10})
            q10 = moved(horn, m0, Q0)
            setj({name: 0})
            about = lambda a: [x + y for x, y in zip(o, rot(sub(Q0, o), z, math.radians(a)))]
            sgn = 1 if norm(sub(q10, about(10))) < 1e-3 else -1
            assert norm(sub(q10, about(sgn * 10))) < 1e-3, "%s: horn joint is not about the servo's Z" % name
            lo, hi = LIMITS[mech]
            T0 = occ[moving].transform2.copy()
            rows = []
            for i in range(9):
                th = lo + (hi - lo) * i / 8
                setj({mech: th})
                P = moved(occ[moving], T0, P0)
                F = lambda ph: norm(sub(about(sgn * ph), P)) - L0
                # the assembly branch: the root nearest home (the other one is the horn flipped past the link)
                roots = [a for a in (x * 0.1 for x in range(-1200, 1200)) if F(a) * F(a + 0.1) <= 0]
                assert roots, "%s: no closure at %s=%g" % (name, mech, th)
                a = min(roots, key=abs)
                b = a + 0.1
                for _ in range(40):
                    c = (a + b) / 2
                    a, b = (a, c) if F(a) * F(c) <= 0 else (c, b)
                rows.append((th, (a + b) / 2))
            setj({mech: 0})
            # mechanism = ratio x horn, least squares through home
            ratio = sum(t * p for t, p in rows) / sum(p * p for t, p in rows)
            print("  %-24s -> %-16s closure %.4f mm (horn r%.2f), link %.3f mm, ratio %.5f %s per horn deg, "
                  "worst %.3f deg" % (name, mech, closure, r, L0, ratio, mech,
                                      max(abs(t - ratio * p) for t, p in rows)))
            print("      " + "  ".join("%+.1f:%+.2f" % (t, p) for t, p in rows))

    if os.environ.get("SV_LINK"):
        for k, (name, (mech, *_)) in enumerate(zip(NAMES, FOURBAR), 1):
            for n in ("%s -> %s" % (name, mech), "%s -> %s" % (mech, name)):
                if root.motionLinks.itemByName(n):
                    root.motionLinks.itemByName(n).deleteMe()
            ratio = RATIOS[name]
            # the mechanism LEADS and the horn follows, though the servo is the input: driving either end works, and
            # a follower keeps its value when a joint that carries it moves (TRAPS: a leading pan horn wandered up
            # to 1.7 deg, or ran to its limit, whenever Tilt was set after it)
            li = root.motionLinks.createInput(J.itemByName(mech), J.itemByName(name))
            li.valueOne = adsk.core.ValueInput.createByString("10 deg")
            li.valueTwo = adsk.core.ValueInput.createByString("%.6f deg" % (10 / abs(ratio)))
            li.isReversed = ratio < 0
            root.motionLinks.add(li).name = "%s -> %s" % (mech, name)
            lo, hi = sorted(v / ratio for v in LIMITS[mech])
            lim = J.itemByName(name).jointMotion.rotationLimits
            lim.isMinimumValueEnabled = lim.isMaximumValueEnabled = True
            lim.minimumValue, lim.maximumValue = math.radians(lo), math.radians(hi)
            lim.restValue = 0
            lim.isRestValueEnabled = True
            print("  link %-17s -> %-24s horn %.5f deg per %s deg, horn limits %.1f..%.1f deg" % (
                mech, name, 1 / ratio, mech, lo, hi))

    drive = os.environ.get("SV_DRIVE")
    if drive:
        vals = {n.strip(): float(v) for n, v in (kv.split("=") for kv in drive.split(","))}
        base = {}
        for n in vals:
            k = NAMES.index(n) + 1
            moving = FOURBAR[k - 1][1]
            base[n] = home(k), occ[moving].transform2.copy(), occ["SG90 Horn native:%d" % k].transform2.copy()
        setj(vals)
        for n, ((P0, Q0, L0, _, r), mT, hT) in base.items():
            k = NAMES.index(n) + 1
            mech, moving = FOURBAR[k - 1][:2]
            P, Q = moved(occ[moving], mT, P0), moved(occ["SG90 Horn native:%d" % k], hT, Q0)
            E = pt(occ[FOURBAR[k - 1][3]].transform2, FOURBAR[k - 1][4])
            z = servo_axis(occ["SG90 native:%d" % k])[1]
            EQ = sub(E, Q)
            print("  %-24s %+7.2f deg -> %-16s %+8.3f deg; coupler would stretch %+.3f mm; the drawn coupler's end is "
                  "%.3f mm across the shaft axis from the horn hole r%.2f" % (n, vals[n], mech,
                                                         math.degrees(J.itemByName(mech).jointMotion.rotationValue),
                                                         norm(sub(P, Q)) - L0,
                                                         math.sqrt(max(0.0, dot(EQ, EQ) - dot(EQ, z) ** 2)), r))
        for i in range(J.count):
            J.item(i).jointMotion.rotationValue = 0
        adsk.doEvents()

    if os.environ.get("SV_SAVE"):
        print("  saved", app.activeDocument.save("SG90 servos and horns: rigid mounts, horn joints, motion links "
                                                 "(servos_native.py)"))

