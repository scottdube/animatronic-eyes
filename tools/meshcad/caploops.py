# Raw boundary loops of the cap at one level, as ordered mesh vertices, for free-form outlines (a logo) that
# profile2d.py's line/arc fit cannot hold to tolerance. Each loop is split at its corners (turn > CORNER deg
# between neighbouring chords) into runs; a run of two points is a line, longer runs go to a fitted spline.
# Keeps only loops whose every vertex lies inside the (u, v) box. Writes JSON {"loops": [[run, ...], ...]},
# each run a list of (u, v) in mm, consecutive runs sharing their end point, the last closing on the first.
# usage: caploops.py stl toolsdir axis level u0 u1 v0 v1 out.json [corner_deg]
import sys, json, math
import numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load

T, N, A = load(sys.argv[1]); ax = int(sys.argv[3]); lvl = float(sys.argv[4])
u0, u1, v0, v1 = map(float, sys.argv[5:9]); out = sys.argv[9]
CORNER = float(sys.argv[10]) if len(sys.argv) > 10 else 20.0
uv_ax = [i for i in range(3) if i != ax]
cap = (np.abs(N[:, ax]) > 0.9999) & (np.abs(T[:, :, ax].mean(1) - lvl) < 1e-3)
key = lambda p: (round(float(p[uv_ax[0]]), 4), round(float(p[uv_ax[1]]), 4))
cnt = {}
for t in T[cap]:
    for i in range(3):
        a, b = key(t[i]), key(t[(i + 1) % 3])
        e = (a, b) if a < b else (b, a)
        cnt[e] = cnt.get(e, 0) + 1
adj = {}
for (a, b), c in cnt.items():
    if c == 1:
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
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
        seen.add(cur); loop.append(cur)
    loops.append(loop)


def collinear_drop(loop):
    """Drop T-junction vertices that sit on a straight chord (cap triangulation splits edges)."""
    out = []
    n = len(loop)
    for i in range(n):
        a, b, c = np.array(loop[i - 1]), np.array(loop[i]), np.array(loop[(i + 1) % n])
        u, w = b - a, c - b
        if abs(u[0] * w[1] - u[1] * w[0]) / (np.linalg.norm(u) * np.linalg.norm(w)) < 1e-6 and u @ w > 0:
            continue
        out.append(loop[i])
    return out


res = []
for loop in loops:
    if not all(u0 <= p[0] <= u1 and v0 <= p[1] <= v1 for p in loop):
        continue
    loop = collinear_drop(loop)
    n = len(loop)
    turn = []
    for i in range(n):
        a, b, c = np.array(loop[i - 1]), np.array(loop[i]), np.array(loop[(i + 1) % n])
        u, w = b - a, c - b
        turn.append(abs(math.degrees(math.atan2(u[0] * w[1] - u[1] * w[0], u @ w))))
    corners = [i for i in range(n) if turn[i] > CORNER]
    # a long chord between two short ones is a straight edge: both its ends are corners
    ln = [math.dist(loop[i], loop[(i + 1) % n]) for i in range(n)]
    med = float(np.median(ln))
    for i in range(n):
        if ln[i] > 4 * med:
            corners += [i, (i + 1) % n]
    corners = sorted(set(corners)) or [0]
    runs = []
    for k, c in enumerate(corners):
        e = corners[(k + 1) % len(corners)]
        idx = list(range(c, e + 1)) if e > c else list(range(c, n)) + list(range(0, e + 1))
        runs.append([loop[i] for i in idx])
    res.append(runs)
    print("loop %d pts, %d corners, runs %s" % (n, len(corners), [len(r) for r in runs]))
json.dump({"loops": res}, open(out, "w"))
