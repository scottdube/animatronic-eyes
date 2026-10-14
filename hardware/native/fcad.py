# Small helpers for building native Fusion solids from decoded mesh dimensions.
# All arguments are in mm; Fusion's internal unit is cm, so everything goes through MM.
# Profiles are drawn in model coordinates and mapped into sketch space with
# modelToSketchSpace, so the XZ-plane sketch flip (sketch y = model -Z) never matters.
import math, struct
import adsk.core, adsk.fusion

MM = 0.1
_IDX = {"x": 0, "y": 1, "z": 2}


def VI(v):
    return adsk.core.ValueInput.createByReal(v)


class Builder:
    def __init__(self, root):
        self.root = root
        self.base = {"x": root.yZConstructionPlane, "y": root.xZConstructionPlane,
                     "z": root.xYConstructionPlane}

    def plane(self, axis, c):
        """Construction plane normal to `axis` at coordinate c (mm). The offset sign of the
        base planes is not documented per plane, so try +c, read the origin back, else -c."""
        if abs(c) < 1e-9:
            return self.base[axis]
        cps = self.root.constructionPlanes
        for sgn in (1, -1):
            pi = cps.createInput()
            pi.setByOffset(self.base[axis], VI(sgn * c * MM))
            pl = cps.add(pi)
            o = pl.geometry.origin
            if abs([o.x, o.y, o.z][_IDX[axis]] - c * MM) < 1e-7:
                return pl
            pl.deleteMe()
        raise RuntimeError(f"could not place plane {axis}={c}")

    @staticmethod
    def to3d(axis, c, u, v):
        return {"x": (c, u, v), "y": (u, c, v), "z": (u, v, c)}[axis]

    def loop(self, name, axis, c, start, segs):
        """One closed loop on the plane axis=c in (u, v) coords: x->(y,z), y->(x,z), z->(x,y).
        segs: ("L", (u,v)) line to point; ("A", (cu,cv), (u,v), dir) arc about centre,
        dir +1 counter-clockwise in (u,v), -1 clockwise. The last segment must end at start."""
        sk = self.root.sketches.add(self.plane(axis, c))
        sk.name = name

        def sp(uv):
            x, y, z = self.to3d(axis, c, uv[0], uv[1])
            return sk.modelToSketchSpace(adsk.core.Point3D.create(x * MM, y * MM, z * MM))

        lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
        cur_uv, cur, first = start, sp(start), None
        for k, s in enumerate(segs):
            end_uv = s[1] if s[0] == "L" else s[2]
            last = k == len(segs) - 1
            if last:
                assert math.dist(end_uv, start) < 1e-6, f"{name}: loop not closed"
            end = first if last else sp(end_uv)
            if s[0] == "L":
                ent = lines.addByTwoPoints(cur, end)
            else:
                (cu, cv), d = s[1], s[3]
                a0 = math.atan2(cur_uv[1] - cv, cur_uv[0] - cu)
                a1 = math.atan2(end_uv[1] - cv, end_uv[0] - cu)
                sweep = ((a1 - a0) * d) % (2 * math.pi)
                am = a0 + d * sweep / 2
                R = math.dist(cur_uv, (cu, cv))
                ent = arcs.addByThreePoints(cur, sp((cu + R * math.cos(am), cv + R * math.sin(am))), end)
            if first is None:
                first = ent.startSketchPoint
            # arcs may come back reversed; continue from whichever end sits at end_uv
            e_pt, s_pt = ent.endSketchPoint, ent.startSketchPoint
            tgt = sp(end_uv)
            cur = e_pt if e_pt.geometry.distanceTo(tgt) < s_pt.geometry.distanceTo(tgt) else s_pt
            if first is not None and k == 0:
                st = sp(start)
                first = s_pt if s_pt.geometry.distanceTo(st) < e_pt.geometry.distanceTo(st) else e_pt
            cur_uv = end_uv
        return sk

    def circle(self, name, axis, c, centre, r):
        sk = self.root.sketches.add(self.plane(axis, c))
        sk.name = name
        x, y, z = self.to3d(axis, c, centre[0], centre[1])
        p = sk.modelToSketchSpace(adsk.core.Point3D.create(x * MM, y * MM, z * MM))
        sk.sketchCurves.sketchCircles.addByCenterRadius(p, r * MM)
        return sk

    @staticmethod
    def profile(sk):
        n = sk.profiles.count
        if n != 1:
            raise RuntimeError(f"sketch {sk.name}: {n} profiles, expected 1")
        return sk.profiles.item(0)

    def extrude(self, sk, axis, lo, hi, op="new", name=None):
        """Extrude the sketch's one profile over axis in [lo, hi] (mm). The sketch must sit
        at the midpoint plane; the extent is symmetric about it."""
        ops = {"new": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
               "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
               "cut": adsk.fusion.FeatureOperations.CutFeatureOperation}
        ei = self.root.features.extrudeFeatures.createInput(self.profile(sk), ops[op])
        ei.setSymmetricExtent(VI((hi - lo) * MM), True)
        f = self.root.features.extrudeFeatures.add(ei)
        if name:
            f.name = name
            if op == "new":
                f.bodies.item(0).name = name
        return f

    def prism(self, name, axis, lo, hi, start, segs, op="new"):
        sk = self.loop(name, axis, (lo + hi) / 2, start, segs)
        return self.extrude(sk, axis, lo, hi, op, name)

    def revolve_z(self, name, start, segs, op="new"):
        """Revolve an (r, z) loop drawn on the XZ plane a full turn about the Z axis."""
        sk = self.loop(name, "y", 0.0, start, segs)
        ops = {"new": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
               "join": adsk.fusion.FeatureOperations.JoinFeatureOperation}
        ri = self.root.features.revolveFeatures.createInput(self.profile(sk), self.root.zConstructionAxis, ops[op])
        ri.setAngleExtent(False, VI(2 * math.pi))
        f = self.root.features.revolveFeatures.add(ri)
        f.name = name
        if op == "new":
            f.bodies.item(0).name = name
        return f

    def combine(self, target, tools, how, name=None):
        oc = adsk.core.ObjectCollection.create()
        for t in tools:
            oc.add(t)
        ci = self.root.features.combineFeatures.createInput(target, oc)
        ci.operation = {"join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
                        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
                        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation}[how]
        ci.isKeepToolBodies = False
        f = self.root.features.combineFeatures.add(ci)
        if name:
            f.name = name
        return f

    def sector(self, name, a0, a1, r=14.0, zlo=-8.0, zhi=4.0):
        """Pie-slice prism from angle a0 to a1 (deg, counter-clockwise) about Z."""
        p0 = (r * math.cos(math.radians(a0)), r * math.sin(math.radians(a0)))
        p1 = (r * math.cos(math.radians(a1)), r * math.sin(math.radians(a1)))
        return self.prism(name, "z", zlo, zhi, (0.0, 0.0),
                          [("L", p0), ("A", (0.0, 0.0), p1, 1), ("L", (0.0, 0.0))])


def _pts(c):
    if isinstance(c, adsk.fusion.SketchLine):
        return [c.startSketchPoint, c.endSketchPoint]
    if isinstance(c, adsk.fusion.SketchArc):
        return [c.startSketchPoint, c.endSketchPoint]
    return []


def _tangent_dir(c, p):
    """Unit tangent of curve c at its end point p, in sketch space (sign ignored)."""
    if isinstance(c, adsk.fusion.SketchLine):
        a, b = c.startSketchPoint.geometry, c.endSketchPoint.geometry
        dx, dy = b.x - a.x, b.y - a.y
    else:
        cc, q = c.centerSketchPoint.geometry, p.geometry
        dx, dy = -(q.y - cc.y), q.x - cc.x
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def constrain_sketch(sk, tan_tol=0.02, log=None):
    """Turn drawn geometry into a constrained, dimensioned sketch without moving it (beyond closing
    fit noise): horizontal/vertical lines, tangency at smooth joints, centres on the origin or on each
    other, a radius or diameter on every arc and circle, then horizontal/vertical distances from the
    sketch origin to whatever points are still free. A dimension the solver rejects as redundant is
    skipped; that greedy order always ends with every point fixed. Returns the number of free points left."""
    gc, dims = sk.geometricConstraints, sk.sketchDimensions
    org = sk.originPoint
    H = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    V = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
    curves = [c for c in sk.sketchCurves if not c.isReference and not c.isConstruction]
    stats = {"hv": 0, "tan": 0, "coin": 0, "rad": 0, "pos": 0, "skip": 0}

    def tryadd(f, *a):
        try:
            r = f(*a)
        except RuntimeError:
            stats["skip"] += 1
            return None
        if r is not None and hasattr(r, "isDriving") and not r.isDriving:
            r.deleteMe()
            stats["skip"] += 1
            return None
        return r

    tol = 1e-6
    for c in curves:
        if isinstance(c, adsk.fusion.SketchLine):
            a, b = c.startSketchPoint.geometry, c.endSketchPoint.geometry
            if abs(a.x - b.x) < tol:
                stats["hv"] += tryadd(gc.addVertical, c) is not None
            elif abs(a.y - b.y) < tol:
                stats["hv"] += tryadd(gc.addHorizontal, c) is not None
    # tangency where two curves meet with the same direction
    by_pt = {}
    for c in curves:
        for p in _pts(c):
            by_pt.setdefault(p.entityToken, (p, []))[1].append(c)
    for p, cs in by_pt.values():
        if len(cs) != 2 or all(isinstance(c, adsk.fusion.SketchLine) for c in cs):
            continue
        u, v = _tangent_dir(cs[0], p), _tangent_dir(cs[1], p)
        if abs(u[0] * v[1] - u[1] * v[0]) < tan_tol:
            stats["tan"] += tryadd(gc.addTangent, cs[0], cs[1]) is not None
    # centres: on the origin, or on an earlier centre
    centres = []
    for c in curves:
        if isinstance(c, (adsk.fusion.SketchArc, adsk.fusion.SketchCircle)):
            cp = c.centerSketchPoint
            g = cp.geometry
            if math.hypot(g.x, g.y) < 1e-5:
                stats["coin"] += tryadd(gc.addCoincident, cp, org) is not None
            else:
                for q in centres:
                    if q.geometry.distanceTo(g) < 1e-5:
                        stats["coin"] += tryadd(gc.addCoincident, cp, q) is not None
                        break
                else:
                    centres.append(cp)
    # equal radii were almost certainly designed equal: one dimension then drives both
    rounds = [c for c in curves if isinstance(c, (adsk.fusion.SketchArc, adsk.fusion.SketchCircle))]
    for i, c in enumerate(rounds):
        for q in rounds[:i]:
            if type(q) is type(c) and abs(q.radius - c.radius) < 2e-5:   # 2e-4 mm
                stats["eq"] = stats.get("eq", 0) + (tryadd(gc.addEqual, q, c) is not None)
                break
    for c in curves:
        if isinstance(c, (adsk.fusion.SketchArc, adsk.fusion.SketchCircle)):
            g = c.centerSketchPoint.geometry
            tp =adsk.core.Point3D.create(g.x + c.radius * 0.8, g.y + c.radius * 0.8, 0)
            f = dims.addDiameterDimension if isinstance(c, adsk.fusion.SketchCircle) else dims.addRadialDimension
            stats["rad"] += tryadd(f, c, tp) is not None
    # positions, centres first
    pts = [c.centerSketchPoint for c in curves if isinstance(c, (adsk.fusion.SketchArc, adsk.fusion.SketchCircle))]
    pts += [p for p, _ in by_pt.values()]
    for p in pts:
        for orient in (H, V):
            if p.isFullyConstrained:
                break
            g = p.geometry
            d = g.x if orient == H else g.y
            if abs(d) < tol:
                f = gc.addVerticalPoints if orient == H else gc.addHorizontalPoints
                stats["pos"] += tryadd(f, org, p) is not None
            else:
                tp = adsk.core.Point3D.create(g.x / 2 if orient == H else g.x + 1, g.y + 1 if orient == H else g.y / 2, 0)
                stats["pos"] += tryadd(dims.addDistanceDimension, org, p, orient, tp) is not None
    free = sum(1 for p in pts if not p.isFullyConstrained)
    if log is not None:
        log.append("%s: %s free %d" % (sk.name, stats, free))
    return free


def constrain_all(comp, log=None):
    """constrain_sketch on every sketch in the component; returns total free points."""
    return sum(constrain_sketch(sk, log=log) for sk in comp.sketches)


def stl_vertices(path):
    """Unique vertices (mm) of a binary STL, pure Python (Fusion's interpreter has no numpy)."""
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    seen = set()
    for i in range(n):
        o = 84 + i * 50 + 12
        v = struct.unpack("<9f", d[o:o + 36])
        for k in range(3):
            seen.add((round(v[3 * k], 4), round(v[3 * k + 1], 4), round(v[3 * k + 2], 4)))
    return sorted(seen)


def vertex_check(body, path, every=1, worst=8, skip=None):
    """Minimum distance (mm) from STL vertices to the body. Returns (max, mean, n, worst list).
    skip(x, y, z) -> True leaves a vertex out (a mesh artefact the spec documents)."""
    mm = adsk.core.Application.get().measureManager
    verts = [v for v in stl_vertices(path)[::every] if not (skip and skip(*v))]
    out = []
    for x, y, z in verts:
        d = mm.measureMinimumDistance(body, adsk.core.Point3D.create(x * MM, y * MM, z * MM)).value / MM
        out.append((d, (x, y, z)))
    out.sort(reverse=True)
    return out[0][0], sum(d for d, _ in out) / len(out), len(out), out[:worst]
