# Constrain and dimension every sketch of saved native designs in place (fcad.constrain_all), check the body did
# not move (volume, distance from STL vertices), save a new hub version and re-export the .f3d next to this file.
# Env CD_ONLY=name,name (document names without " native"); CD_REOPEN=1 discards local edits first by closing the
# document unsaved and reopening the hub version. Run through the Fusion MCP, one or two parts per call.
import os, sys
import adsk.core, adsk.fusion

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    "/Users/scottdube/code/animatronic-eyes/hardware/native"
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import importlib, fcad
importlib.reload(fcad)

KIT = os.path.join(HERE, "..", "kit-stl")
# part: (hub lineage id, STL, vertex stride)
DOCS = {
    "Eye Adaptor": ("urn:adsk.wipprod:dm.lineage:vnTyd9ibS7KepCqSyOfSmA", "Eye Adaptor (x2)", 13),
    "Bottom Lid Link": ("urn:adsk.wipprod:dm.lineage:bS8BA4IvReejwi1XGS0wTA", "Bottom Lid Link (x2)", 1),
    "Top Lid Link": ("urn:adsk.wipprod:dm.lineage:dzPIztYnTRaxZKw_aaa1DQ", "Top Lid Link (x2)", 1),
    "Y-Arm": ("urn:adsk.wipprod:dm.lineage:9BhDALwaQzOH2UoVc8FQ9g", "Y-Arm", 1),
    "Three-Point Connector": ("urn:adsk.wipprod:dm.lineage:Sj5WMw0mQyeQ-aD7u6x2mA", "Three-Point Connector", 1),
    "Fork": ("urn:adsk.wipprod:dm.lineage:yHAy1LAdRR-g1Dhq42awRg", "Fork (x2)", 1),
}


def run(_context):
    app = adsk.core.Application.get()
    only = [s for s in os.environ.get("CD_ONLY", "").split(",") if s] or list(DOCS)
    for part in only:
        fid, stl, every = DOCS[part]
        name = part + " native"
        docs = [d for d in app.documents if d.isSaved and d.dataFile.id == fid]
        if docs and os.environ.get("CD_REOPEN"):
            docs[0].close(False)
            docs = []
        doc = docs[0] if docs else app.documents.open(app.data.findFileById(fid))
        doc.activate()
        des = adsk.fusion.Design.cast(app.activeProduct)
        root = des.rootComponent
        body = root.bRepBodies.item(0)
        v0 = body.volume
        log = []
        free = fcad.constrain_all(root, log)
        bad = [s.name for s in root.sketches if not s.isFullyConstrained]
        assert free == 0 and not bad, (part, free, bad, log)
        # tangency and equal radii close the fit noise (5 ppm on the Top Lid Link); the vertex check is the guard
        assert abs(body.volume - v0) < 1e-4 * v0, (part, v0, body.volume)
        mx, mean, n, _ = fcad.vertex_check(body, os.path.join(KIT, stl + ".stl"), every, 1)
        assert mx < 0.002, (part, mx)
        ndim = sum(s.sketchDimensions.count for s in root.sketches)
        print("%s: %d sketches fully constrained, %d dimensions, vol %.4f, vertex max %.4f (n=%d)" % (
            name, root.sketches.count, ndim, body.volume, mx, n))
        em = des.exportManager
        em.execute(em.createFusionArchiveExportOptions(os.path.join(HERE, name + ".f3d")))
        print("  save", doc.save("Sketches constrained and dimensioned (fcad.constrain_all)"))
