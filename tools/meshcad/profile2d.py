# Plate profile extractor: boundary loops of the cap at one level, segmented into lines and arcs.
# Mesh vertices lie on the true curves, so an arc is a run of short, near-equal chords turning the same
# way; its circle is fitted through all of the run's vertices. Prints each loop and a JSON form that
# fcad.Builder.loop accepts. usage: profile2d.py stl toolsdir axis level [tol]
import sys, numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load

T, N, A = load(sys.argv[1]); ax = int(sys.argv[3]); lvl = float(sys.argv[4])
tol = float(sys.argv[5]) if len(sys.argv) > 5 else 0.003
uv_ax = [i for i in range(3) if i != ax]
cap = (np.abs(N[:, ax]) > 0.9999) & (np.abs(T[:, :, ax].mean(1) - lvl) < 1e-3)
key = lambda p: (round(p[uv_ax[0]], 4), round(p[uv_ax[1]], 4))
cnt = {}
for t in T[cap]:
    for i in range(3):
        a, b = key(t[i]), key(t[(i + 1) % 3])
        e = (a, b) if a < b else (b, a)
        cnt[e] = cnt.get(e, 0) + 1
# boundary edges: used once. Collinear T-junctions can split an edge, so chain by adjacency.
bnd = [e for e, c in cnt.items() if c == 1]
adj = {}
for a, b in bnd:
    adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
loops, seen = [], set()
for start in adj:
    if start in seen: continue
    loop, prev, cur = [start], None, start
    seen.add(start)
    while True:
        nxt = [p for p in adj[cur] if p != prev and (p not in seen or (p == start and len(loop) > 2))]
        if not nxt: break
        prev, cur = cur, nxt[0]
        if cur == start: break
        loop.append(cur); seen.add(cur)
    loops.append(np.array(loop))


from seg2d import report
report(loops, tol)
