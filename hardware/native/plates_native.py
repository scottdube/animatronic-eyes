# Native Fusion rebuilds of the kit's plate linkages: each is one profile extruded through its thickness.
# Profiles come from tools/meshcad/profile2d.py (cap boundary -> lines and arcs, fit residual <= 0.0001 mm)
# and live in profiles/<slug>.json in the STL's own frame, so the result drops into the kit assembly as is.
# Run through the Fusion MCP: one NEW design per part, body named "<part> native", then the volume and
# the distance from every STL vertex to the body. Env PL_ONLY=slug,slug limits the run; PL_STL_DIR writes
# a High-refinement STL of each result for tools/meshcad/thickdiff.py. Saving is left to the caller.
import json, math, os, struct, sys
import adsk.core, adsk.fusion

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    "/Users/scottdube/code/animatronic-eyes/hardware/native"
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import importlib, fcad
importlib.reload(fcad)
from fcad import Builder

KIT = os.path.join(HERE, "..", "kit-stl")
# slug: (STL name, extrusion axis, thickness range in mm)
PARTS = {
    "bottom-lid-link": ("Bottom Lid Link (x2)", "x", (-16.435, -14.435)),
    "top-lid-link": ("Top Lid Link (x2)", "x", (-16.435, -14.435)),
    "y-arm": ("Y-Arm", "x", (0.0, 3.0)),
    "three-point-connector": ("Three-Point Connector", "y", (5.1, 7.1)),
}


def stl_volume_cm3(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    v = 0.0
    for i in range(n):
        a = struct.unpack("<9f", d[84 + i * 50 + 12:84 + i * 50 + 48])
        v += (a[0] * (a[4] * a[8] - a[5] * a[7]) - a[1] * (a[3] * a[8] - a[5] * a[6])
              + a[2] * (a[3] * a[7] - a[4] * a[6])) / 6
    return v / 1000


def loop_area(start, segs):
    pts = [start] + [s[1] if s[0] == "L" else s[2] for s in segs]
    return 0.5 * abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1] for i in range(len(pts) - 1)))


def is_circle(start, segs):
    return len(segs) == 1 and segs[0][0] == "A" and math.dist(segs[0][2], start) < 1e-6


def build(root, slug):
    name, axis, (lo, hi) = PARTS[slug]
    loops = json.load(open(os.path.join(HERE, "profiles", slug + ".json")))
    loops = [(tuple(st), [(s[0], tuple(s[1])) if s[0] == "L" else (s[0], tuple(s[1]), tuple(s[2]), s[3])
                          for s in sg]) for st, sg in loops]
    loops.sort(key=lambda l: -loop_area(*l) if not is_circle(*l) else -math.pi * math.dist(l[0], l[1][0][1]) ** 2)
    b = Builder(root)
    title = name.replace(" (x2)", "") + " native"
    body = b.prism("Profile", axis, lo, hi, *loops[0]).bodies.item(0)
    for k, (st, sg) in enumerate(loops[1:], 1):
        if is_circle(st, sg):
            sk = b.circle(f"Hole {k}", axis, (lo + hi) / 2, sg[0][1], math.dist(st, sg[0][1]))
            b.extrude(sk, axis, lo, hi, "cut", f"Hole {k}")
        else:
            b.prism(f"Cutout {k}", axis, lo, hi, st, sg, op="cut")
    body.name = title
    return body, title, os.path.join(KIT, name + ".stl")


def run(_context):
    app = adsk.core.Application.get()
    only = [s for s in os.environ.get("PL_ONLY", "").split(",") if s] or list(PARTS)
    out_dir = os.environ.get("PL_STL_DIR")
    for slug in only:
        title = PARTS[slug][0].replace(" (x2)", "") + " native"
        for d in list(app.documents):  # drop an unsaved earlier attempt
            if d.name.startswith(title) and not d.isSaved:
                d.close(False)
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name = title
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        body, title, stl = build(design.rootComponent, slug)
        if out_dir:
            o = design.exportManager.createSTLExportOptions(body, os.path.join(out_dir, slug + ".stl"))
            o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            o.sendToPrintUtility = False
            design.exportManager.execute(o)
        mx, mean, n, worst = fcad.vertex_check(body, stl, 1, 3)
        print("%-24s solid %s vol %.4f cm3 (STL %.4f)  vertices n=%d max %.4f mean %.5f mm  worst %s" % (
            title, body.isSolid, body.volume, stl_volume_cm3(stl), n, mx, mean,
            "; ".join("%.4f@(%.2f,%.2f,%.2f)" % (d, *p) for d, p in worst)))
