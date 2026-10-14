"""Check a part spec (axis-aligned extrusions) against its STL without Fusion.

usage: xcsg.py spec.py toolsdir [stl]   (stl defaults to the spec's STL)

A spec module holds STL (path relative to the spec file) and FEATURES: a list of dicts
    name, op ("new" | "join" | "cut"), axis ("x" | "y" | "z"), lo, hi (mm along the axis), and either
    loop=(start, segs)      segs as fcad.Builder.loop takes them, in (u, v): x->(y,z), y->(x,z), z->(x,y)
    circle=((cu, cv), r)
    runs=[[(u, v), ...], ...]   a closed outline as runs of mesh vertices (caploops.py); spec_native draws a
                            two-point run as a line and a longer one as a fitted spline, here each is chords
    revolve=dict(centre=(cu, cv), pts=[(r, w), ...], a0=deg, a1=deg)   about the axis line through (cu, cv),
                            angle from +u toward +v; lo/hi unused
or op "chamfer": a Fusion chamfer feature (spec_native.py selects the edges); here its `csg` list of ordinary
features stands in for it.
hardware/native/spec_native.py builds the same list in Fusion. Here it is built with manifold3d, then the STL's
solid is subtracted both ways and every leftover blob is listed with its volume and bounding box: "missing" is
material the STL has and the spec does not, "extra" the reverse. A finished spec leaves only facet slivers
(the STL's chords cut inside true arcs, so "missing" slivers are expected on convex arcs and "extra" on concave).
"""
import sys, os, math, importlib.util
import numpy as np
import manifold3d as mf

sys.path.insert(0, sys.argv[2])
from stlmesh import load


def arc_points(p0, c, p1, d, step=math.radians(0.5)):
    a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
    a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
    sweep = ((a1 - a0) * d) % (2 * math.pi) or 2 * math.pi
    R = math.dist(p0, c)
    n = max(2, int(sweep / step))
    return [(c[0] + R * math.cos(a0 + d * sweep * k / n), c[1] + R * math.sin(a0 + d * sweep * k / n))
            for k in range(1, n + 1)]


def polygon(f):
    if "circle" in f:
        (cu, cv), r = f["circle"]
        n = 720
        return [(cu + r * math.cos(2 * math.pi * k / n), cv + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    if "runs" in f:
        return [tuple(p) for run in f["runs"] for p in run[:-1]]
    start, segs = f["loop"]
    pts, cur = [tuple(start)], tuple(start)
    for s in segs:
        if s[0] == "L":
            cur = tuple(s[1])
            pts.append(cur)
        else:
            pts += arc_points(cur, s[1], s[2], s[3])
            cur = tuple(s[2])
    assert math.dist(pts[-1], pts[0]) < 1e-6, f"{f['name']}: loop not closed"
    return pts[:-1]


# (u, v, w) -> model, w along the axis (the y case is a reflection; manifold re-winds those itself)
PERM = {"x": [[0, 0, 1], [1, 0, 0], [0, 1, 0]], "y": [[1, 0, 0], [0, 0, 1], [0, 1, 0]],
        "z": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}


def feature_solid(f):
    P = np.array(PERM[f["axis"]], float)
    m = np.zeros((3, 4))
    m[:, :3] = P
    if "revolve" in f:
        r = f["revolve"]
        cs = mf.CrossSection([np.array(r["pts"], float)], mf.FillRule.EvenOdd)
        s = mf.Manifold.revolve(cs, 720, r["a1"] - r["a0"]).rotate((0, 0, r["a0"]))
        m[:, 3] = P @ np.array([r["centre"][0], r["centre"][1], 0.0])
    else:
        cs = mf.CrossSection([np.array(polygon(f), float)], mf.FillRule.EvenOdd)
        s = mf.Manifold.extrude(cs, f["hi"] - f["lo"]).translate((0, 0, f["lo"]))
    s = s.transform(m)
    assert s.volume() > 0 and s.status() == mf.Error.NoError, f["name"]
    return s


def build(features, body=None):
    for f in features:
        if f["op"] == "chamfer":
            body = build(f["csg"], body)
            continue
        s = feature_solid(f)
        if f["op"] == "new":
            body = s if body is None else body + s
        elif f["op"] == "join":
            body = body + s
        else:
            body = body - s
    return body


def stl_solid(path):
    T = load(path)[0].astype(np.float64)
    V, inv = np.unique(np.round(T.reshape(-1, 3), 5), axis=0, return_inverse=True)
    m = mf.Manifold(mf.Mesh(vert_properties=V.astype(np.float32), tri_verts=inv.reshape(-1, 3).astype(np.uint32)))
    assert m.status() == mf.Error.NoError, m.status()
    return m


def blobs(m, label, show=12, floor=0.05):
    parts = sorted(m.decompose(), key=lambda p: -p.volume())
    tot = sum(p.volume() for p in parts)
    big = [p for p in parts if p.volume() > floor]
    print(f"{label}: {tot:.3f} mm3 in {len(parts)} pieces, {len(big)} over {floor} mm3")
    for p in big[:show]:
        b = p.bounding_box()
        print(f"   {p.volume():9.3f}  [{b[0]:.3f} {b[1]:.3f} {b[2]:.3f}] .. [{b[3]:.3f} {b[4]:.3f} {b[5]:.3f}]")
    return tot


def main():
    spec_path = sys.argv[1]
    spec = importlib.util.spec_from_file_location("spec", spec_path)
    S = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S)
    stl = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(spec_path)), S.STL)
    body = build(S.FEATURES)
    ref = stl_solid(stl)
    print(f"spec volume {body.volume():.3f}  STL volume {ref.volume():.3f}  genus {body.genus()} / {ref.genus()}")
    blobs(ref - body, "missing")
    blobs(body - ref, "extra")


if __name__ == "__main__":
    main()
