# Native Fusion rebuild of the kit's Fork, in the STL's own frame (plate normal Y, stem up Z).
# Decoded with tools/meshcad/plate.py + profile2d.py (docs/linkages-cad.md): a 2 mm plate whose arms straddle the
# Eye Adaptor's lugs on the same (+-5.8594, -1.95) axis, a stem to a round end at z 14.5 with a boss on +Y, and a
# 0.5 x 1.5 chamfer on the outer edge of the +Y face. Every non-cap, non-wall triangle of the mesh lies on that
# chamfer (0.949 r + 0.316 y = 8.5). The chamfer is a Fusion chamfer feature, so it stays editable.
# Run through the Fusion MCP: NEW design "Fork native", prints volume and the distance from every STL vertex to
# the body. Env FK_STL writes a High-refinement STL for tools/meshcad/thickdiff.py. Saving is left to the caller.
import math, os, sys
import adsk.core, adsk.fusion

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    "/Users/scottdube/code/animatronic-eyes/hardware/native"
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import importlib, fcad
importlib.reload(fcad)
from fcad import Builder, MM, VI

STL = os.path.join(HERE, "..", "kit-stl", "Fork (x2).stl")
TITLE = "Fork native"

Y0, Y1, Y2 = 1.3, 3.3, 4.8   # back face, front face, boss top
R_OUT = 8.3594               # outer arc about the Y axis; arms' outer faces at |x| = R_OUT
R_IN = 3.3594                # inner arc between the arms; arms' inner faces and stem sides at |x| = R_IN
Z_ARM = -4.9                 # arm ends
Z_TOP = 14.5                 # stem round-end centre (R_IN), boss centre
ARM_HOLE = (5.8594, -1.95, 1.75)   # x (mirrored), z, radius: the Eye Adaptor lug-hole axis
TOP_HOLE_R = 1.5
CH_FACE, CH_DEPTH = 0.5, 1.5  # chamfer: inset on the +Y face, depth down the outer wall


def outline():
    zj = math.sqrt(R_OUT ** 2 - R_IN ** 2)   # outer arc meets the stem sides
    return (R_IN, zj), [
        ("L", (R_IN, Z_TOP)), ("A", (0.0, Z_TOP), (-R_IN, Z_TOP), 1), ("L", (-R_IN, zj)),
        ("A", (0.0, 0.0), (-R_OUT, 0.0), 1), ("L", (-R_OUT, Z_ARM)), ("L", (-R_IN, Z_ARM)), ("L", (-R_IN, 0.0)),
        ("A", (0.0, 0.0), (R_IN, 0.0), -1), ("L", (R_IN, Z_ARM)), ("L", (R_OUT, Z_ARM)), ("L", (R_OUT, 0.0)),
        ("A", (0.0, 0.0), (R_IN, zj), 1)]


def chamfer_edges(body):
    """Outer edges of the +Y face: the R_OUT arcs and the |x| = R_OUT lines."""
    oc = adsk.core.ObjectCollection.create()
    for e in body.edges:
        p0, p1 = e.startVertex.geometry, e.endVertex.geometry
        if abs(p0.y - Y1 * MM) > 1e-6 or abs(p1.y - Y1 * MM) > 1e-6:
            continue
        g = e.geometry
        if isinstance(g, adsk.core.Arc3D) and abs(g.radius - R_OUT * MM) < 1e-6:
            oc.add(e)
        elif isinstance(g, adsk.core.Line3D) and abs(abs(p0.x) - R_OUT * MM) < 1e-6 and abs(abs(p1.x) - R_OUT * MM) < 1e-6:
            oc.add(e)
    return oc


def build(root):
    b = Builder(root)
    body = b.prism("Plate", "y", Y0, Y1, *outline()).bodies.item(0)
    b.extrude(b.circle("Boss", "y", (Y1 + Y2) / 2, (0.0, Z_TOP), R_IN), "y", Y1, Y2, "join", "Boss")
    x, z, r = ARM_HOLE
    for s in (1, -1):
        b.extrude(b.circle(f"Arm hole {'+' if s > 0 else '-'}X", "y", (Y0 + Y1) / 2, (s * x, z), r),
                  "y", Y0, Y1, "cut", f"Arm hole {'+' if s > 0 else '-'}X")
    b.extrude(b.circle("Top hole", "y", (Y0 + Y2) / 2, (0.0, Z_TOP), TOP_HOLE_R), "y", Y0, Y2, "cut", "Top hole")
    edges = chamfer_edges(body)
    assert edges.count == 4, f"chamfer edges {edges.count}"
    cf = root.features.chamferFeatures
    # which face takes distance one is not documented per edge; build it, read the +Y face's outer radius
    # back (must be R_OUT - CH_FACE), and flip if the distances landed the other way round
    for flip in (False, True):
        ci = cf.createInput2()
        ci.chamferEdgeSets.addTwoDistancesChamferEdgeSet(edges, VI(CH_FACE * MM), VI(CH_DEPTH * MM), flip, True)
        f = cf.add(ci)
        f.name = "Outer chamfer"
        xs = [abs(v.geometry.x) for v in body.vertices if abs(v.geometry.y - Y1 * MM) < 1e-6]
        if abs(max(xs) - (R_OUT - CH_FACE) * MM) < 1e-6:
            break
        f.deleteMe()
        edges = chamfer_edges(body)
    else:
        raise RuntimeError("chamfer distances did not land on either orientation")
    body.name = TITLE
    return body


def run(_context):
    app = adsk.core.Application.get()
    for d in list(app.documents):  # drop an unsaved earlier attempt
        if d.name.startswith(TITLE) and not d.isSaved:
            d.close(False)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = TITLE
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    body = build(design.rootComponent)
    out = os.environ.get("FK_STL")
    if out:
        o = design.exportManager.createSTLExportOptions(body, out)
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        o.sendToPrintUtility = False
        design.exportManager.execute(o)
    mx, mean, n, worst = fcad.vertex_check(body, STL, 1, 5)
    print("%s solid %s vol %.4f cm3  vertices n=%d max %.4f mean %.5f mm  worst %s" % (
        TITLE, body.isSolid, body.volume, n, mx, mean,
        "; ".join("%.4f@(%.2f,%.2f,%.2f)" % (d, *p) for d, p in worst)))
