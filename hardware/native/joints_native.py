# Joints for "EyeMech assembly", so the eyes and lids move. Run through the Fusion MCP on the open assembly (built by
# assembly_native.py). The pivots were read off the placed parts' cylinders (2026-10-14), not assumed; every pin runs
# through a Ø3 hole in the part that holds it and a Ø3.5 clearance hole in the part that turns on it:
#   Tilt   Sub Base (with the Eye Holder screwed to it) turns on two pins from the Main Base's inner walls, about X
#          through both eye centres. Both eyes go up/down together; servo 1 drives it through the Y-Arm.
#   Pan    each Eye Adaptor turns on a vertical pin in the Eye Holder at its eye centre. The Fork is pinned to the
#          Adaptor's two lugs (two parallel pins = rigid) and the eye snaps on, so the three move as one. The
#          Three-Point Connector ties both Fork tails (z 14.5) to servo 0, so the eyes pan together.
#   Lids   each lid's ears turn on pins from the Main Base walls, about the same X axis as Tilt, but on the Main Base:
#          a lid does not follow the eyes. Each has its own servo and lid link.
# Not modelled: the servo horns. Each coupler (Three-Point Connector, Y-Arm, four lid links) is pinned at its
# mechanism end and motion-linked to counter-rotate, so it keeps its orientation and its servo end slides past where
# the horn would be. Fusion solves trees, not the closed four-bar loops of the real linkage.
# Env:
#   JN_BUILD  1 = snap the Y-Arm onto its Sub Base pin, add rigid groups, joints and motion links
#   JN_DRIVE  "Pan L=20,Tilt=-15,..." = set those joints (deg), print every occurrence that moved, then put all back
#   JN_SAVE   1 = save a new version of the assembly
import math, os
import adsk.core, adsk.fusion

RIGID = [["Main Base native:1", "Servo Block native:1"],
         ["Sub Base native:1", "Eye Holder native:1"],
         ["Eye Adaptor native:1", "Fork native:1", "PlaceHolder Eye native:1"],
         ["Eye Adaptor native:2", "Fork native:2", "PlaceHolder Eye native:2"]]

# name, turning occurrence, holding occurrence, (occurrence whose hole is the axis, axis, radius mm, (u, v) mm): the
# hole's axis runs along `axis` through u, v = (y, z) for X or (x, z) for Y, in assembly coordinates
JOINTS = [
    ("Tilt", "Sub Base native:1", "Main Base native:1", ("Sub Base native:1", "X", 2.0, (0, 0))),
    ("Pan L", "Eye Adaptor native:1", "Eye Holder native:1", ("Eye Holder native:1", "Y", 1.75, (0, 0))),
    ("Pan R", "Eye Adaptor native:2", "Eye Holder native:1", ("Eye Holder native:1", "Y", 1.75, (75, 0))),
    ("Top Left Lid", "Top Left Lid native:1", "Main Base native:1", ("Top Left Lid native:1", "X", 1.75, (0, 0))),
    ("Top Right Lid", "Top Right Lid native:1", "Main Base native:1", ("Top Right Lid native:1", "X", 1.75, (0, 0))),
    ("Bottom Left Lid", "Bottom Left Lid native:1", "Main Base native:1",
     ("Bottom Left Lid native:1", "X", 1.75, (0, 0))),
    ("Bottom Right Lid", "Bottom Right Lid native:1", "Main Base native:1",
     ("Bottom Right Lid native:1", "X", 1.75, (0, 0))),
    ("Three-Point Connector", "Three-Point Connector native:1", "Fork native:1", ("Fork native:1", "Y", 1.5, (0, 14.5))),
    ("Y-Arm", "Y-Arm native:1", "Sub Base native:1", ("Sub Base native:1", "X", 1.5, (10.47, 0))),
    ("Top Lid Link L", "Top Lid Link native:1", "Top Left Lid native:1",
     ("Top Left Lid native:1", "X", 1.0, (15.79, 3.278))),
    ("Top Lid Link R", "Top Lid Link native:2", "Top Right Lid native:1",
     ("Top Right Lid native:1", "X", 1.0, (15.79, 3.278))),
    ("Bottom Lid Link L", "Bottom Lid Link native:1", "Bottom Left Lid native:1",
     ("Bottom Left Lid native:1", "X", 1.0, (-15.608, 3.951))),
    ("Bottom Lid Link R", "Bottom Lid Link native:2", "Bottom Right Lid native:1",
     ("Bottom Right Lid native:1", "X", 1.0, (-15.608, 3.951))),
]

# leader, follower, reversed: Pan R follows Pan L; each coupler counter-rotates against the joint it rides on
LINKS = [("Pan L", "Pan R", False), ("Pan L", "Three-Point Connector", True), ("Tilt", "Y-Arm", True),
         ("Top Left Lid", "Top Lid Link L", True), ("Top Right Lid", "Top Lid Link R", True),
         ("Bottom Left Lid", "Bottom Lid Link L", True), ("Bottom Right Lid", "Bottom Lid Link R", True)]


def hole(occ, axis, radius, uv, tol=0.05):
    """the first cylindrical face of occ (assembly context) with this radius, its axis along `axis` through uv (mm)"""
    for f in occ.bRepBodies.item(0).faces:
        g = f.geometry
        if g.surfaceType != adsk.core.SurfaceTypes.CylinderSurfaceType or abs(g.radius * 10 - radius) > 0.01:
            continue
        a, o = g.axis, g.origin
        a.normalize()
        along, (i, j) = ((abs(a.x), (1, 2)) if axis == "X" else (abs(a.y), (0, 2)))
        p = [o.x * 10, o.y * 10, o.z * 10]
        if along > 0.99999 and abs(p[i] - uv[0]) < tol and abs(p[j] - uv[1]) < tol:
            return f, (p[i], p[j])
    raise LookupError("%s: no R%s hole along %s through %s" % (occ.name, radius, axis, uv))


def rotation_deg(m):
    a = m.asArray()
    return math.degrees(math.acos(max(-1.0, min(1.0, (a[0] + a[5] + a[10] - 1) / 2))))


def run(_context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    occ = {root.occurrences.item(i).name: root.occurrences.item(i) for i in range(root.occurrences.count)}
    print(app.activeDocument.name, len(occ), "occurrences,", root.asBuiltJoints.count, "as-built joints")

    if os.environ.get("JN_BUILD"):
        assert root.asBuiltJoints.count == 0 and root.joints.count == 0, "joints already exist"
        # The Complete Model poses the Y-Arm with its pivot hole 1.2 mm off the Sub Base pin it turns on. Move it onto
        # the pin first; an as-built joint keeps whatever pose it is given, so it would turn about the wrong line.
        _, (y0, z0) = hole(occ["Y-Arm native:1"], "X", 1.75, (10.71, 1.2), tol=0.1)
        _, (y1, z1) = hole(occ["Sub Base native:1"], "X", 1.5, (10.47, 0))
        t = occ["Y-Arm native:1"].transform2
        t.translation = adsk.core.Vector3D.create(t.translation.x, t.translation.y + (y1 - y0) / 10,
                                                  t.translation.z + (z1 - z0) / 10)
        occ["Y-Arm native:1"].transform2 = t
        print("  Y-Arm snapped by (0, %.4f, %.4f) mm = %.4f mm" % (y1 - y0, z1 - z0, math.hypot(y1 - y0, z1 - z0)))
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()

        for names in RIGID:
            c = adsk.core.ObjectCollection.create()
            for n in names:
                c.add(occ[n])
            g = root.rigidGroups.add(c, False)
            g.name = names[0].replace(" native:", " ") + " group"
        made = {}
        for name, moving, fixed, (owner, axis, r, uv) in JOINTS:
            face, _ = hole(occ[owner], axis, r, uv)
            geo = adsk.fusion.JointGeometry.createByNonPlanarFace(face, adsk.fusion.JointKeyPointTypes.MiddleKeyPoint)
            ji = root.asBuiltJoints.createInput(occ[moving], occ[fixed], geo)
            ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            j = root.asBuiltJoints.add(ji)
            j.name = name
            made[name] = j
        for lead, follow, rev in LINKS:
            li = root.motionLinks.createInput(made[lead], made[follow])
            li.valueOne = adsk.core.ValueInput.createByString("90 deg")
            li.valueTwo = adsk.core.ValueInput.createByString("90 deg")
            li.isReversed = rev
            root.motionLinks.add(li).name = "%s -> %s" % (lead, follow)
        print("  %d rigid groups, %d as-built joints, %d motion links" % (
            root.rigidGroups.count, root.asBuiltJoints.count, root.motionLinks.count))

    drive = os.environ.get("JN_DRIVE")
    if drive:
        before = {n: o.transform2 for n, o in occ.items()}
        for item in drive.split(","):
            n, v = item.split("=")
            root.asBuiltJoints.itemByName(n.strip()).jointMotion.rotationValue = math.radians(float(v))
        adsk.doEvents()
        # The one loop the joint tree does not close: the right Fork's tail pin must stay in the connector's hole
        # (found by radius alone: tilted, no axis is along Y any more; the tail hole is the Fork's only R1.5 face)
        cyl = lambda o, r: [g for g in occ[o].bRepBodies.item(0).faces
                            if g.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType
                            and abs(g.geometry.radius * 10 - r) < 0.01]
        f, = cyl("Fork native:2", 1.5)
        c = cyl("Three-Point Connector native:1", 1.75)
        p, a = f.geometry.origin, f.geometry.axis
        a.normalize()
        def off(q):
            v = p.vectorTo(q.geometry.origin)
            t = v.dotProduct(a)
            return math.sqrt(max(0.0, v.length ** 2 - t * t)) * 10
        print("  Fork R tail pin to nearest connector hole axis: %.4f mm" % min(off(g) for g in c))
        for n, o in occ.items():
            m0, m1 = before[n], o.transform2
            d = m0.copy()
            d.invert()
            d.transformBy(m1)    # m1 * m0^-1: the occurrence's motion in assembly coordinates
            moved = m1.translation.copy()
            moved.subtract(m0.translation)
            ang = rotation_deg(d)
            if ang > 1e-4 or moved.length > 1e-6:
                print("  %-30s turned %8.4f deg, origin moved %7.4f mm" % (n, ang, moved.length * 10))
        for i in range(root.asBuiltJoints.count):
            root.asBuiltJoints.item(i).jointMotion.rotationValue = 0
        adsk.doEvents()
        back = max(max(abs(p - q) for p, q in zip(before[n].asArray(), o.transform2.asArray())) for n, o in occ.items())
        print("  all joints back to 0: max transform change %.2e" % back)

    if os.environ.get("JN_SAVE"):
        print("  saved", app.activeDocument.save("Joints: tilt, pan L/R, four lids, couplers (joints_native.py)"))
