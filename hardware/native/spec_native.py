# Build a part spec (hardware/native/specs/<slug>.py, checked first with tools/meshcad/xcsg.py) as a native Fusion
# design: one sketch + extrude (or full-turn revolve) per feature, an optional closing Move (FRAME), Fusion chamfer features where the spec says chamfer, every sketch
# constrained and dimensioned (fcad.constrain_all), then the STL vertex check.
# Run through the Fusion MCP. Env:
#   SP_SPEC  spec slug, e.g. sub_base (required)
#   SP_STL   write a High-refinement STL of the body here, for tools/meshcad/thickdiff.py
#   SP_SAVE  1 = save to the hub folder "Basic EyeMech kit" as "<Part> native" and export the .f3d next to this file
import importlib.util, os, sys
import adsk.core, adsk.fusion

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    "/Users/scottdube/code/animatronic-eyes/hardware/native"
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import importlib, fcad
importlib.reload(fcad)
from fcad import Builder, MM, VI

KIT_FILE = "urn:adsk.wipprod:dm.lineage:lA3puJqMQu26yQnhI1_h-w"   # faceted "Eye Adaptor (x2)": its folder is the kit's
_IDX = {"x": 0, "y": 1, "z": 2}


def load_spec(slug):
    path = os.path.join(HERE, "specs", slug + ".py")
    sp = importlib.util.spec_from_file_location("spec_" + slug, path)
    S = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(S)
    S.STL_PATH = os.path.normpath(os.path.join(os.path.dirname(path), S.STL))
    return S


def chamfer(root, body, f):
    """Equal-distance chamfer on the body edges lying in the plane f['face'], except those lying in f['skip'];
    or, with f['pick'] (points in mm), on the edge through each point plus its tangent chain."""
    oc = adsk.core.ObjectCollection.create()
    if f.get("pick"):
        for p in f["pick"]:
            pt = adsk.core.Point3D.create(*(c * MM for c in p))
            hits = body.parentComponent.findBRepUsingPoint(pt, adsk.fusion.BRepEntityTypes.BRepEdgeEntityType,
                                                          1e-4, True)
            assert hits.count == 1, f"{f['name']}: {hits.count} edges at {p}"
            oc.add(hits.item(0))
        cf = root.features.chamferFeatures
        ci = cf.createInput2()
        ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(oc, VI(f["d"] * MM), True)
        ft = cf.add(ci)
        ft.name = f["name"]
        return sum(1 for e in ft.faces)
    ax, c = _IDX[f["face"][0]], f["face"][1] * MM
    sk = (_IDX[f["skip"][0]], f["skip"][1] * MM) if f.get("skip") else None
    on = lambda p, k, v: abs([p.x, p.y, p.z][k] - v) < 1e-6
    for e in body.edges:
        ends = [e.startVertex.geometry, e.endVertex.geometry]
        if all(on(p, ax, c) for p in ends) and not (sk and all(on(p, *sk) for p in ends)):
            oc.add(e)
    assert oc.count, f"{f['name']}: no edges in {f['face']}"
    cf = root.features.chamferFeatures
    ci = cf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(oc, VI(f["d"] * MM), True)
    ft = cf.add(ci)
    ft.name = f["name"]
    return oc.count


def build(root, S):
    b = Builder(root)
    body = None
    for f in S.FEATURES:
        if f["op"] == "chamfer":
            n = chamfer(root, body, f)
            print("  %s: %d %s" % (f["name"], n, "faces" if f.get("pick") else "edges"))
            continue
        if f["op"] == "rotate":    # second drawing frame: turn what is built so far (see xcsg.py)
            b.rotate_body(body, f["axis"], f["deg"], f["name"])
            continue
        mid = (f["lo"] + f["hi"]) / 2
        if "revolve" in f:
            r = f["revolve"]
            if "loop" not in r or r.get("a1", 360.0) - r.get("a0", 0.0) != 360.0:
                raise RuntimeError(f"{f['name']}: Fusion revolves take a full-turn loop= half-section")
            ft = b.revolve(f["name"], f["axis"], r["centre"], *r["loop"], op=f["op"])
        elif "circle" in f:
            ft = b.extrude(b.circle(f["name"], f["axis"], mid, *f["circle"]), f["axis"], f["lo"], f["hi"],
                           f["op"], f["name"])
        elif "runs" in f:
            ft = b.extrude(b.runs_loop(f["name"], f["axis"], mid, f["runs"]), f["axis"], f["lo"], f["hi"],
                           f["op"], f["name"])
        elif "loop" in f:
            ft = b.prism(f["name"], f["axis"], f["lo"], f["hi"], *f["loop"], op=f["op"])
        else:
            raise RuntimeError(f"{f['name']}: no Fusion form for this feature")
        if f["op"] == "new":
            body = ft.bodies.item(0)
        assert root.bRepBodies.count == 1, f"{f['name']}: {root.bRepBodies.count} bodies"
    if getattr(S, "FRAME", None):   # drawn in a turned frame (the eyelids): one Move turns it into the STL's
        b.rotate_body(body, S.FRAME[0], S.FRAME[1], "Frame %s %+g deg" % S.FRAME)
    body.name = S.TITLE
    fcad.constrain_all(root)
    return body


def run(_context):
    app = adsk.core.Application.get()
    S = load_spec(os.environ["SP_SPEC"])
    for d in list(app.documents):  # drop an unsaved earlier attempt
        if d.name.startswith(S.TITLE) and not d.isSaved:
            d.close(False)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = S.TITLE
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    body = build(root, S)
    bad = [s.name for s in root.sketches if not s.isFullyConstrained]
    ndim = sum(s.sketchDimensions.count for s in root.sketches)
    out = os.environ.get("SP_STL")
    if out:
        o = design.exportManager.createSTLExportOptions(body, out)
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        o.sendToPrintUtility = False
        design.exportManager.execute(o)
    # EXEMPT: boxes ((x0, y0, z0), (x1, y1, z1)) of STL vertices that are mesh artefacts, each with its reason
    boxes = [e["box"] for e in getattr(S, "EXEMPT", [])]
    inbox = lambda x, y, z: any(all(a <= c <= b for a, c, b in zip(lo, (x, y, z), hi)) for lo, hi in boxes)
    mx, mean, n, worst = fcad.vertex_check(body, S.STL_PATH, 1, 5, inbox if boxes else None)
    print("%s solid %s vol %.4f cm3  %d sketches (%d not fully constrained), %d dimensions" % (
        S.TITLE, body.isSolid, body.volume, root.sketches.count, len(bad), ndim))
    print("  vertices n=%d (%d exempt boxes) max %.4f mean %.5f mm  worst %s" % (
        n, len(boxes), mx, mean, "; ".join("%.4f@(%.2f,%.2f,%.2f)" % (d, *p) for d, p in worst)))
    if os.environ.get("SP_SAVE"):
        assert mx < 0.002 and not bad, "not saving: check failed"
        em = design.exportManager
        em.execute(em.createFusionArchiveExportOptions(os.path.join(HERE, S.TITLE + ".f3d")))
        folder = app.data.findFileById(KIT_FILE).parentFolder
        print("  saved", doc.saveAs(S.TITLE, folder, S.DESCRIPTION, ""))
