"""Convert the Will Cogley Basic EyeMech kit STLs into Fusion designs.

For each printable part in hardware/kit-stl/ (Complete Model.stl is skipped:
it is a reference assembly and non-manifold where parts touch):
  1. new design document, mesh inserted in mm through a base feature
  2. Convert Mesh, Faceted method (Prismatic needs the Design Extension,
     which this licence does not have; see docs/eyeball-cad.md)
  3. .f3d exported to hardware/kit-f3d/
  4. saved to the hub folder "Basic EyeMech kit" (created if missing) in the
     project that holds the open "Eye model" document, else the active project
  5. document closed

Everything is logged to hardware/kit-f3d/import_log.txt. One part failing does
not stop the others; the script raises at the end if any failed.
Set SAVE_TO_HUB = False to only export the .f3d files.
"""
import adsk.core, adsk.fusion
import os, time, traceback

REPO = os.path.expanduser("~/code/animatronic-eyes")
STL_DIR = os.path.join(REPO, "hardware", "kit-stl")
OUT_DIR = os.path.join(REPO, "hardware", "kit-f3d")
HUB_FOLDER = "Basic EyeMech kit"
SAVE_TO_HUB = True
SKIP = {"Complete Model.stl"}

_log = None


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line)
    _log.write(line + "\n")
    _log.flush()


def hub_folder(app):
    project = None
    for doc in app.documents:
        if doc.name.startswith("Eye model") and doc.dataFile:
            project = doc.dataFile.parentProject
            break
    if project is None:
        project = app.data.activeProject
    root = project.rootFolder
    for i in range(root.dataFolders.count):
        f = root.dataFolders.item(i)
        if f.name == HUB_FOLDER:
            log(f"hub: using {project.name}/{HUB_FOLDER}")
            return f
    log(f"hub: creating {project.name}/{HUB_FOLDER}")
    return root.dataFolders.add(HUB_FOLDER)


def set_faceted(inp):
    """Pick the Faceted method by introspection; log what was found."""
    enum_cls = None
    for n in dir(adsk.fusion):
        if "MeshConvert" in n and "Method" in n:
            enum_cls = getattr(adsk.fusion, n)
            break
    attrs = [a for a in dir(inp) if "ethod" in a and not a.startswith("_")]
    if enum_cls is None or not attrs:
        log(f"  method: left at default (enum={enum_cls}, attrs={attrs})")
        return
    members = [m for m in dir(enum_cls) if "Faceted" in m]
    if not members:
        log(f"  method: no Faceted member in {enum_cls.__name__}: {dir(enum_cls)}")
        return
    setattr(inp, attrs[0], getattr(enum_cls, members[0]))
    log(f"  method: {attrs[0]} = {enum_cls.__name__}.{members[0]}")


def convert_one(app, stl, folder):
    name = os.path.splitext(stl)[0]
    part = name.replace(" (x2)", "")
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent

    bf = root.features.baseFeatures.add()
    bf.startEdit()
    root.meshBodies.add(os.path.join(STL_DIR, stl),
                        adsk.fusion.MeshUnits.MillimeterMeshUnit, bf)
    bf.finishEdit()
    bf.name = "Kit STL"
    mesh = root.meshBodies.item(root.meshBodies.count - 1)
    log(f"  mesh: {mesh.mesh.triangleCount} triangles")

    coll = adsk.core.ObjectCollection.create()
    coll.add(mesh)
    mcf = root.features.meshConvertFeatures
    inp = mcf.createInput(coll)
    set_faceted(inp)
    feat = mcf.add(inp)

    bodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    if not bodies:
        raise RuntimeError("Convert Mesh produced no solid body")
    for i, b in enumerate(bodies):
        b.name = part if len(bodies) == 1 else f"{part} {i + 1}"
        log(f"  body: {b.name}  solid={b.isSolid}  faces={b.faces.count}  "
            f"volume={b.volume:.4f} cm3")
    for i in range(root.meshBodies.count):
        root.meshBodies.item(i).isLightBulbOn = False

    f3d = os.path.join(OUT_DIR, name + ".f3d")
    em = design.exportManager
    em.execute(em.createFusionArchiveExportOptions(f3d))
    log(f"  f3d: {os.path.basename(f3d)}  {os.path.getsize(f3d)} bytes")

    if SAVE_TO_HUB:
        doc.saveAs(name, folder, "Will Cogley Basic EyeMech kit part, "
                   "STL converted Faceted (CC BY-NC-SA 4.0)", "")
        log(f"  hub: saved as {HUB_FOLDER}/{name}")
    doc.close(False)


def run(context):
    global _log
    app = adsk.core.Application.get()
    os.makedirs(OUT_DIR, exist_ok=True)
    _log = open(os.path.join(OUT_DIR, "import_log.txt"), "w")
    log(f"Fusion {app.version}")
    failed = []
    try:
        folder = hub_folder(app) if SAVE_TO_HUB else None
        stls = sorted(f for f in os.listdir(STL_DIR)
                      if f.lower().endswith(".stl") and f not in SKIP)
        log(f"{len(stls)} STLs")
        for stl in stls:
            log(stl)
            try:
                convert_one(app, stl, folder)
            except Exception:
                failed.append(stl)
                log("  FAILED\n" + traceback.format_exc())
        log(f"done: {len(stls) - len(failed)} ok, {len(failed)} failed {failed}")
    finally:
        _log.close()
    if failed:
        raise RuntimeError(f"{len(failed)} part(s) failed, see import_log.txt")
