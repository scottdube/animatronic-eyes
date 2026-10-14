# Joint limits for "EyeMech assembly" from collisions, not from guesses: drive a joint (or several together) out from
# home until Fusion's interference analysis reports any body overlapping another, then bisect to 0.1 deg. Run through
# the Fusion MCP on the open assembly after joints_native.py. Every joint is put back to 0 at the end. Env:
#   CL_SWEEP  "pan:Pan L=1|open L+:Top Left Lid=1,Bottom Left Lid=-1@Tilt=-30|..."  label:joint=sign,...[@held pose]
#             per sweep; runs both ways (+ and -) unless the label ends in "+" or "-"
#   CL_POSES  "Pan L=30,Tilt=-20|..."  interference at each pose (for the corners of the limits)
#   CL_LIMITS "Pan L=-30:30|..."  set rotation limits (deg); "Pan L=off" clears them; "apply" sets LIMITS below
#   CL_IGNORE "Y-Arm native:1,..." occurrences left out of the interference check (to see past an approximated coupler)
#   CL_MAX    sweep range in deg (default 120); CL_STEP coarse step (default 2)
import math, os
import adsk.core, adsk.fusion

# The limits set on the hub assembly (2026-10-14), deg. Each is the measured stop with the other joints at home; see
# docs/native-parts-cad.md for what stops each one, and for the one coupled collision no per-joint limit can express
# (eyes down with the top lids open). Lid "closed" is where both lids of an eye meet closing together; "open" is the
# most both can open together at any pan with tilt 0. CL_LIMITS=apply sets these.
LIMITS = {"Pan L": (-44.8, 41.9), "Pan R": (-44.8, 41.9), "Tilt": (-32.3, 29.5),
          "Top Left Lid": (-25.7, 24.4), "Top Right Lid": (-24.4, 25.7),
          "Bottom Left Lid": (-24.4, 25.7), "Bottom Right Lid": (-25.7, 24.4)}


def interferences(design, root):
    c = adsk.core.ObjectCollection.create()
    skip = {n.strip() for n in os.environ.get("CL_IGNORE", "").split(",")}
    for i in range(root.occurrences.count):
        if root.occurrences.item(i).name not in skip:
            c.add(root.occurrences.item(i).bRepBodies.item(0))
    ii = design.createInterferenceInput(c)
    ii.areCoincidentFacesIncluded = False

    # A result's entity can come back as the component's native body (assemblyContext None), which does not say
    # which of two occurrences (Fork native:1 or :2) it was: take the one whose box holds the overlap's centre.
    def who(entity, overlap):
        if entity.assemblyContext:
            return entity.assemblyContext.name
        b = overlap.boundingBox
        p = adsk.core.Point3D.create(*((getattr(b.minPoint, k) + getattr(b.maxPoint, k)) / 2 for k in "xyz"))
        for i in range(root.occurrences.count):
            o = root.occurrences.item(i)
            if o.component == entity.parentComponent and o.bRepBodies.item(0).boundingBox.contains(p):
                return o.name
        return entity.parentComponent.name + ":?"
    return [(who(r.entityOne, r.interferenceBody), who(r.entityTwo, r.interferenceBody),
             r.interferenceBody.volume * 1000) for r in design.analyzeInterference(ii)]


def pose(root, values):
    J = root.asBuiltJoints
    for i in range(J.count):
        J.item(i).jointMotion.rotationValue = 0
    for n, v in values.items():
        J.itemByName(n).jointMotion.rotationValue = math.radians(v)
    adsk.doEvents()
    # A value outside a joint's limits is ignored, not clamped: the joint stays where it was, so read every one back
    for n, v in values.items():
        got = math.degrees(J.itemByName(n).jointMotion.rotationValue)
        if abs(got - v) > 1e-6:
            raise ValueError("%s: asked %g deg, joint is at %g (outside its limits?)" % (n, v, got))


def parse(s):
    return {k.strip(): float(v) for k, v in (kv.split("=") for kv in s.split(",") if kv.strip())}


def run(_context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    J = root.asBuiltJoints
    try:
        specs = os.environ.get("CL_LIMITS", "")
        if specs == "apply":
            specs = "|".join("%s=%g:%g" % (n, lo, hi) for n, (lo, hi) in LIMITS.items())
        for spec in filter(None, specs.split("|")):
            n, rng = spec.split("=")
            lim = J.itemByName(n.strip()).jointMotion.rotationLimits
            if rng == "off":
                lim.isMinimumValueEnabled = lim.isMaximumValueEnabled = False
            else:
                lo, hi = (math.radians(float(v)) for v in rng.split(":"))
                lim.isMinimumValueEnabled = lim.isMaximumValueEnabled = True
                lim.minimumValue, lim.maximumValue = lo, hi
                lim.restValue = 0
                lim.isRestValueEnabled = True
            print("  limit %-18s %s" % (n, rng))

        for spec in filter(None, os.environ.get("CL_POSES", "").split("|")):
            pose(root, parse(spec))
            hits = interferences(design, root)
            print("  pose %-60s %s" % (spec, "clear" if not hits else
                  "; ".join("%s x %s %.3f mm3" % h for h in hits)))

        top, step = float(os.environ.get("CL_MAX", 120)), float(os.environ.get("CL_STEP", 2))
        for spec in filter(None, os.environ.get("CL_SWEEP", "").split("|")):
            label, drive = spec.split(":", 1)
            drive, _, fixed = drive.partition("@")       # "...@Pan L=41.9": sweep with these joints held
            signs, fixed = parse(drive), parse(fixed)
            ways = [1] if label.endswith("+") else [-1] if label.endswith("-") else [1, -1]
            for way in ways:
                at = lambda a: pose(root, dict(fixed, **{n: way * s * a for n, s in signs.items()})) or \
                    interferences(design, root)
                a, hits = 0.0, []
                while a < top:
                    hits = at(a + step)
                    if hits:
                        break
                    a += step
                if not hits:
                    print("  sweep %-22s %s  clear to %g deg" % (label, "+" if way > 0 else "-", top))
                    continue
                lo, hi = a, a + step          # clear at lo, hit at hi
                while hi - lo > 0.1:
                    mid = (lo + hi) / 2
                    if at(mid):
                        hi = mid
                    else:
                        lo = mid
                hits = at(hi)
                print("  sweep %-22s %s  clear to %6.1f deg; at %.1f: %s" % (
                    label, "+" if way > 0 else "-", way * lo, way * hi,
                    "; ".join("%s x %s %.4f mm3" % h for h in hits)))
    finally:
        pose(root, {})
