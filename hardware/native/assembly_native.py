# Build "EyeMech assembly": every kit part occurrence in placements.json (tools/meshcad/placements.py, fitted against
# Complete Model.stl), inserted as a REFERENCE to its "<Part> native" design in the hub folder "Basic EyeMech kit", so
# an edit to a native part shows up here. The natives are built in their STL's frame, which is the frame placements.json
# moves, so each occurrence's transform is the placement matrix as it stands (mm -> cm). Every matrix is a rigid
# motion: placements.py composes the right eye's mirrored plates and lids into one, so no occurrence is reflected.
# Run through the Fusion MCP. Env:
#   AS_NEW    1 = start a new design document (otherwise insert into the active one)
#   AS_RANGE  "a:b" = insert placements[a:b] (unset: insert nothing; a failed call rolls back its inserts)
#   AS_CHECK  n = vertex check of every occurrence, every n-th kit STL vertex (see below)
#   AS_STL    export the whole root as one STL here, for the check against Complete Model.stl
#   AS_SAVE   1 = save to the hub folder as "EyeMech assembly"; AS_STEP 1 = export "EyeMech assembly.step" next to this
#             file, the local copy (a Fusion archive of a referencing assembly holds no part geometry; TRAPS)
import json, os
import adsk.core, adsk.fusion

HERE = "/Users/scottdube/code/animatronic-eyes/hardware/native"
KIT_FILE = "urn:adsk.wipprod:dm.lineage:lA3puJqMQu26yQnhI1_h-w"   # faceted "Eye Adaptor (x2)": its folder is the kit's
TITLE = "EyeMech assembly"
DESCRIPTION = "Basic EyeMech assembled from the native parts (hardware/native/assembly_native.py, placements.json)"


def native_name(part):
    return part.replace(" (x2)", "") + " native"


def orthonormal(M):
    """placements.json keeps 7 digits, so a fitted rotation is off orthonormal by up to 1e-7, and addByInsert rejects
    that as 'invalid argument transform'. Gram-Schmidt the rows; it moves a point 50 mm out by ~5e-6 mm."""
    r0, r1 = [M[0][:3], M[1][:3]]
    dot = lambda u, v: sum(p * q for p, q in zip(u, v))
    unit = lambda u: [c / dot(u, u) ** 0.5 for c in u]
    r0 = unit(r0)
    r1 = unit([c - dot(r1, r0) * d for c, d in zip(r1, r0)])
    r2 = [r0[1] * r1[2] - r0[2] * r1[1], r0[2] * r1[0] - r0[0] * r1[2], r0[0] * r1[1] - r0[1] * r1[0]]
    assert dot(r2, M[2][:3]) > 0.999999, "row 2 is not the cross product of rows 0 and 1"
    return [r + [M[i][3]] for i, r in enumerate((r0, r1, r2))] + [M[3]]


def run(_context):
    app = adsk.core.Application.get()
    folder = app.data.findFileById(KIT_FILE).parentFolder
    files = {}
    for i in range(folder.dataFiles.count):
        d = folder.dataFiles.item(i)
        assert d.name not in files, "two hub files named %r" % d.name
        files[d.name] = d

    if os.environ.get("AS_NEW"):
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc = app.activeDocument
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    P = json.load(open(os.path.join(HERE, "placements.json")))
    rng = os.environ.get("AS_RANGE")
    a, b = (int(s) if s else None for s in rng.split(":")) if rng else (0, 0)
    for e in P[a:b]:
        M = orthonormal(e["matrix"])
        assert abs(M[3][3] - 1) < 1e-12, e["occurrence"]
        m = adsk.core.Matrix3D.create()
        m.setWithArray([M[r][c] * (0.1 if c == 3 and r < 3 else 1.0) for r in range(4) for c in range(4)])
        assert m.determinant > 0.999, "%s: reflected" % e["occurrence"]
        occ = root.occurrences.addByInsert(files[native_name(e["part"])], m, True)
        print("  %-22s <- %-28s %s" % (e["occurrence"], occ.name, e["kind"]))
    print("%d occurrences in %s" % (root.occurrences.count, doc.name))

    # AS_CHECK=n: every n-th vertex of each part's kit STL, moved by its placement, measured against that occurrence's
    # body in place: the per-part vertex gate repeated in the assembly, so it checks the transform and the reference
    # both. (An STL of the assembly against the kit meshes reads the kit's chord sag, up to 0.21 mm, not placement.)
    if os.environ.get("AS_CHECK"):
        import sys
        sys.path.insert(0, HERE)
        import fcad
        mm = app.measureManager
        stride = int(os.environ["AS_CHECK"])
        occs = [root.occurrences.item(i) for i in range(root.occurrences.count)]
        used = set()
        for e in P:
            occ = next(o for o in occs if o.component.name == native_name(e["part"]) and o.name not in used)
            used.add(occ.name)
            M = e["matrix"]
            body = occ.bRepBodies.item(0)
            worst = (-1.0, ())
            for x, y, z in fcad.stl_vertices(os.path.join(HERE, "..", "kit-stl", e["part"] + ".stl"))[::stride]:
                p = [sum(M[r][c] * v for c, v in enumerate((x, y, z))) + M[r][3] for r in range(3)]
                d = mm.measureMinimumDistance(body, adsk.core.Point3D.create(*(c * 0.1 for c in p))).value * 10
                worst = max(worst, (d, (x, y, z)))
            print("  check %-22s %-26s max %.4f mm at part %s" % (e["occurrence"], occ.name, worst[0],
                                                                   tuple(round(c, 3) for c in worst[1])))

    out = os.environ.get("AS_STL")
    if out:
        o = design.exportManager.createSTLExportOptions(root, out)
        o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        o.sendToPrintUtility = False
        o.isOneFilePerBody = False
        design.exportManager.execute(o)
        print("  stl", out)

    if os.environ.get("AS_SAVE"):
        assert root.occurrences.count == len(P), "not saving: %d of %d occurrences" % (root.occurrences.count, len(P))
        root.occurrences.item(0).isGrounded = True
        print("  saved", doc.saveAs(TITLE, folder, DESCRIPTION, ""))
    if os.environ.get("AS_STEP"):
        em = design.exportManager
        print("  step", em.execute(em.createSTEPExportOptions(os.path.join(HERE, TITLE + ".step"), root)))
