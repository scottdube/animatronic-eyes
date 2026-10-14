# Plane section of a closed mesh: loops where the plane axis=level cuts the triangles, segmented into lines and
# arcs like profile2d.py (which only sees cap faces). Pick a level between features, not on a cap.
# Where a curved wall's facets twist along the axis, slice points fall inside the true curve and an arc comes out
# in fragments with drifting centres: take exact radii from profile2d.py on a cap or levels.py, not from here.
# (Dropping every point that came from a facet diagonal was tried and rejected: on big planar faces the
# diagonals carry the true corners.)
# usage: section2d.py stl toolsdir axis level [tol]
import sys, numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load
from seg2d import report

T, N, A = load(sys.argv[1]); ax = int(sys.argv[3]); lvl = float(sys.argv[4])
tol = float(sys.argv[5]) if len(sys.argv) > 5 else 0.003
uv = [i for i in range(3) if i != ax]
h = T[:, :, ax] - lvl
assert not np.any(np.abs(h) < 1e-9), "level sits on a vertex; move it off"
key = lambda p: (round(p[0], 5), round(p[1], 5))
adj = {}
for t, s in zip(T, h):
    if (s > 0).all() or (s < 0).all():
        continue
    pts = []
    for i in range(3):
        j = (i + 1) % 3
        if (s[i] > 0) != (s[j] > 0):
            a, b = (i, j) if tuple(t[i]) < tuple(t[j]) else (j, i)   # same edge, same arithmetic, same point
            f = (lvl - t[a][ax]) / (t[b][ax] - t[a][ax])
            p = t[a] + f * (t[b] - t[a])
            pts.append(key(p[uv]))
    p, q = pts
    adj.setdefault(p, []).append(q); adj.setdefault(q, []).append(p)
loops, seen = [], set()
for start in adj:
    if start in seen:
        continue
    loop, prev, cur = [start], None, start
    seen.add(start)
    while True:
        nxt = [p for p in adj[cur] if p != prev and p not in seen]
        if not nxt:
            break
        prev, cur = cur, nxt[0]
        loop.append(cur); seen.add(cur)
    loops.append(np.array(loop))
report(loops, tol)
