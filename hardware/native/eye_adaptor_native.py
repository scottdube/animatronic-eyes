# Native Fusion rebuild of Cogley's "Eye Adaptor (x2)" from the decode in docs/eye-adaptor-cad.md.
# Run through the Fusion MCP (or Shift+S): it opens a NEW design, builds body "Eye Adaptor native" in the
# STL's own frame (Z up, base underside z = -6.7, mirror-symmetric about y = 0), then reports the volume
# and the distance from every STL vertex to the body. Saving is left to the caller.
import math, os, sys
import adsk.core, adsk.fusion

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    "/Users/scottdube/code/animatronic-eyes/hardware/native"
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import importlib, fcad
importlib.reload(fcad)
from fcad import Builder

STL = os.path.join(HERE, "..", "kit-stl", "Eye Adaptor (x2).stl")
FACETED_CM3 = 1.5492


def mirror_x(start, segs):
    """Mirror an (x, z) loop to -x. Arcs flip direction because the traversal keeps its order."""
    m = lambda p: (-p[0], p[1])
    out = []
    for s in segs:
        out.append(("L", m(s[1])) if s[0] == "L" else ("A", m(s[1]), m(s[2]), -s[3]))
    return m(start), out


def build(root):
    b = Builder(root)
    body = b.extrude(b.circle("Base", "z", -5.95, (0, 0), 11.7), "z", -6.7, -5.2, name="Eye Adaptor native").bodies.item(0)
    joins = []

    # side lugs: XZ profile round the hole axis (5.859, -1.95), y -3.1 .. 1.0
    lug = ((3.609, -5.2), [("L", (3.609, -1.95)), ("A", (5.859, -1.95), (5.859, 0.30), -1),
                           ("L", (6.949, 0.30)), ("A", (5.859, -1.95), (8.359, -1.95), -1),
                           ("L", (8.359, -5.2)), ("L", (3.609, -5.2))])
    # gusset: plan triangle (z prism) to y = -3.0, 0.1 past the lug's back face (vertices sit on the
    # dome at y = -3.0),  intersected with an R2.5 dome round the same axis (y prism)
    # The dome's inner end is a flat from the centre lug (3.5, -0.024) down to where it meets R2.5.
    dome = ((3.5, -5.2), [("L", (3.5, -0.024)), ("L", (4.0825, -0.191)),
                          ("A", (5.859, -1.95), (8.359, -1.95), -1),
                          ("L", (8.359, -5.2)), ("L", (3.5, -5.2))])
    for side, (st, sg) in (("+X", lug), ("-X", mirror_x(*lug))):
        joins.append(b.prism(f"Side lug {side}", "y", -3.1, 1.0, st, sg).bodies.item(0))
    for sgn, side in ((1, "+X"), (-1, "-X")):
        tri = b.prism(f"Gusset {side}", "z", -5.2, 1.0, (sgn * 3.5, -3.0),
                      [("L", (sgn * 8.1, -3.0)), ("L", (sgn * 3.5, -7.6)), ("L", (sgn * 3.5, -3.0))]).bodies.item(0)
        st, sg = dome if sgn > 0 else mirror_x(*dome)
        d = b.prism(f"Gusset dome {side}", "y", -8.0, -3.0, st, sg).bodies.item(0)
        b.combine(tri, [d], "intersect")
        joins.append(tri)

    # centre lug: R3.5 top round (0, 0), y -8.1 .. -3.0
    joins.append(b.prism("Centre lug", "y", -8.1, -3.0, (-3.5, -5.2),
                         [("L", (3.5, -5.2)), ("L", (3.5, 0.0)), ("A", (0, 0), (-3.5, 0.0), 1),
                          ("L", (-3.5, -5.2))]).bodies.item(0))
    # centre ramp: YZ triangle over x +-3.5
    joins.append(b.prism("Centre ramp", "x", -3.5, 3.5, (-11.1, -5.2),
                         [("L", (-8.1, -5.2)), ("L", (-8.1, -0.2)), ("L", (-11.1, -5.2))]).bodies.item(0))

    # snap fingers: ring wall (revolve) intersected with an XZ profile Q and a YZ profile S
    ring = ((8.652, -5.2), [("L", (8.946, -4.906)), ("L", (10.3413, -4.3279)),
                            ("A", (10.15, -3.8659), (10.65, -3.8659), 1), ("L", (10.65, 3.0)),
                            ("L", (11.7, 3.0)), ("L", (11.7, -5.2)), ("L", (8.652, -5.2))])
    q_plus = ((5.011, -5.5), [("L", (5.011, -5.2)), ("A", (5.011, -4.45), (5.761, -4.45), 1),
                              ("L", (5.761, 0.5)), ("A", (7.761, 0.5), (7.761, 2.5), -1),
                              ("L", (13, 2.5)), ("L", (13, -5.5)), ("L", (5.011, -5.5))])
    q_minus = ((-13, -5.5), [("L", (-7.019, -5.5)), ("L", (-7.019, -5.2)), ("L", (-8.019, -4.2)),
                             ("L", (-8.019, 1.0)), ("A", (-9.519, 1.0), (-9.519, 2.5), 1),
                             ("L", (-13, 2.5)), ("L", (-13, -5.5))])
    # Finger top: one circle for both fingers, centred 0.026 OFF the mirror plane (fit residual 0.0015 on
    # both sides; a y = 0 centre left 0.04 at the ends). The slot fillets R2 at y = +-3.5 are tangent to it,
    # so their centre heights differ: -1.017 at +y, -0.996 at -y (mesh wall ends read -1.018 / -0.997).
    C, R, RF = (0.0264, 7.7818), 7.4598, 2.0
    h = math.sqrt(R * R - (2.5 - C[1]) ** 2)
    ye_p, ye_m = C[0] + h, C[0] - h

    def fillet(fy):
        fz = C[1] - math.sqrt((R + RF) ** 2 - (fy - C[0]) ** 2)
        k = R / (R + RF)
        return (fy, fz), (C[0] + (fy - C[0]) * k, C[1] + (fz - C[1]) * k)

    (fp, tp), (fm, tm) = fillet(3.5), fillet(-3.5)
    s_plus = ((-13, -5.5), [("L", (13, -5.5)), ("L", (13, 2.5)), ("L", (ye_p, 2.5)),
                            ("A", C, tp, -1), ("A", fp, (1.5, fp[1]), 1),
                            ("L", (1.5, -3.7)), ("A", (0, -3.7), (-1.5, -3.7), -1),
                            ("L", (-1.5, fm[1])), ("A", fm, tm, 1),
                            ("A", C, (ye_m, 2.5), -1), ("L", (-13, 2.5)), ("L", (-13, -5.5))])
    s_minus = ((-13, -5.5), [("L", (13, -5.5)), ("L", (13, 2.5)), ("L", (ye_p, 2.5)),
                             ("A", C, (ye_m, 2.5), -1), ("L", (-13, 2.5)), ("L", (-13, -5.5))])
    for side, q, s, xr in (("+X", q_plus, s_plus, (5.0, 13.0)), ("-X", q_minus, s_minus, (-13.0, -5.0))):
        f = b.revolve_z(f"Finger {side}", *ring).bodies.item(0)
        b.combine(f, [b.prism(f"Finger Q {side}", "y", -14, 14, *q).bodies.item(0)], "intersect")
        b.combine(f, [b.prism(f"Finger S {side}", "x", xr[0], xr[1], *s).bodies.item(0)], "intersect")
        joins.append(f)

    # barbs: revolved ramp cut to three sectors with radial ends
    barb = ((11.7, -4.753), [("L", (12.199, -1.124)), ("L", (12.199, 0.376)), ("L", (11.7, 0.376)),
                             ("L", (11.7, -4.753))])
    for a0, a1 in ((19.5, 60.5), (-60.5, -19.5), (134.5, 225.5)):
        bb = b.revolve_z(f"Barb {a0:g}", *barb).bodies.item(0)
        b.combine(bb, [b.sector(f"Barb sector {a0:g}", a0, a1).bodies.item(0)], "intersect")
        joins.append(bb)

    b.combine(body, joins, "join", "Join all")

    # holes and the -X slot
    for sgn in (1, -1):
        # y -3.0 .. 1.0, not the lug's -3.1: the gusset closes the last 0.1 (column check, thickdiff.py)
        b.extrude(b.circle(f"Lug hole {sgn:+d}", "y", -1.0, (sgn * 5.859, -1.95), 1.5), "y", -3.0, 1.0, "cut")
    b.extrude(b.circle("Centre hole", "y", -5.5, (0, 0), 1.5), "y", -8.0, -3.0, "cut")
    b.prism("Rib slot", "z", -8.0, 5.0, (-14, -0.925),
            [("L", (-11.3654, -0.925)), ("A", (-11.3654, 0), (-11.3654, 0.925), 1),
             ("L", (-14, 0.925)), ("L", (-14, -0.925))], op="cut")
    body.name = "Eye Adaptor native"
    fcad.constrain_all(root)
    return body


def run(_context):
    app = adsk.core.Application.get()
    for d in list(app.documents):  # drop an unsaved earlier attempt
        if d.name.startswith("Eye Adaptor native") and not d.isSaved:
            d.close(False)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "Eye Adaptor native"
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    body = build(root)
    print("bodies", root.bRepBodies.count, "solid", body.isSolid,
          "volume cm3 %.4f (faceted %.4f)" % (body.volume, FACETED_CM3))
    out = os.environ.get("EA_STL")  # optional fine STL of the result, for tools/meshcad/thickdiff.py
    if out:
        o = design.exportManager.createSTLExportOptions(body, out)
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        o.sendToPrintUtility = False
        design.exportManager.execute(o)
    every = int(os.environ.get("EA_EVERY", "13"))
    mx, mean, n, worst = fcad.vertex_check(body, STL, every)
    print("vertex check n=%d max %.4f mm mean %.4f mm" % (n, mx, mean))
    for d, p in worst:
        print("  %.4f at (%.3f, %.3f, %.3f)" % (d, *p))
