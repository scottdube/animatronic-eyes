# Plate profile extractor: boundary loops of the cap at one level, segmented into lines and arcs.
# Mesh vertices lie on the true curves, so an arc is a run of short, near-equal chords turning the same
# way; its circle is fitted through all of the run's vertices. Prints each loop and a JSON form that
# fcad.Builder.loop accepts. usage: profile2d.py stl toolsdir axis level [tol]
import sys, json, math, numpy as np
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


def area(P):
    x, y = P[:, 0], P[:, 1]
    return 0.5 * (x * np.roll(y, -1) - np.roll(x, -1) * y).sum()


def circfit(P):
    M = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
    (cx, cy, c), *_ = np.linalg.lstsq(M, (P ** 2).sum(1), rcond=None)
    R = math.sqrt(c + cx * cx + cy * cy)
    return (cx, cy), R, np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - R).max()


def segment(P):
    """Drop collinear points, then group chords into arcs. Returns (start, segs) for fcad."""
    n = len(P)
    keep = []
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) / (np.linalg.norm(b - a) * np.linalg.norm(c - b)) > 1e-4:
            keep.append(b)
    P = np.array(keep); n = len(P)
    L = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)            # chord i: P[i] -> P[i+1]
    d = np.roll(P, -1, 0) - P
    turn = np.arctan2(np.roll(d[:, 0], 1) * d[:, 1] - np.roll(d[:, 1], 1) * d[:, 0],
                      (np.roll(d, 1, 0) * d).sum(1))              # turn at P[i], from chord i-1 to i
    # start at the longest chord (almost always a line) so no arc wraps the seam
    s0 = int(np.argmax(L)); P, L, turn = np.roll(P, -s0, 0), np.roll(L, -s0), np.roll(turn, -s0)
    segs, i = [], 0
    while i < n:
        j = i  # try to grow an arc over chords i..j
        best = None
        while j + 1 < n:
            j += 1
            idx = list(range(i, j + 2)) if j + 1 < n else list(range(i, n)) + [0]
            Q = P[[k % n for k in idx]]
            if j > i and (max(L[i:j + 1]) / min(L[i:j + 1]) > 1.6 or
                          np.any(np.sign(turn[i + 1:j + 1]) != np.sign(turn[i + 1]))):
                break
            c, R, res = circfit(Q)
            if res > tol: break
            best = (j, c, R, res)
        if best is not None and best[0] > i:
            j, c, R, res = best
            end = P[(j + 1) % n]
            # direction: sign of the turn
            dirn = 1 if turn[i + 1] > 0 else -1
            segs.append(("A", (round(c[0], 4), round(c[1], 4)), (round(end[0], 4), round(end[1], 4)), dirn,
                         round(R, 4), round(res, 4), j - i + 1))
            i = j + 1
        else:
            end = P[(i + 1) % n]
            segs.append(("L", (round(end[0], 4), round(end[1], 4))))
            i += 1
    return (round(P[0][0], 4), round(P[0][1], 4)), merge(segs)


def merge(segs, tol=0.002):
    """One arc can come out as arc, chord-as-line, arc when a single tessellation chord is longer than
    its neighbours. Fold any line whose far end lies on the previous arc's circle, and any arc that
    continues the previous one (same centre, radius, direction), into that arc."""
    out = []
    for s in segs:
        if out and out[-1][0] == "A":
            c, R = out[-1][1], out[-1][4]
            on = lambda p: abs(math.dist(p, c) - R) < tol
            if (s[0] == "L" and on(s[1])) or \
               (s[0] == "A" and math.dist(s[1], c) < tol and abs(s[4] - R) < tol and s[3] == out[-1][3]):
                out[-1] = ("A", c, s[1] if s[0] == "L" else s[2], out[-1][3], R, out[-1][5],
                           out[-1][6] + (1 if s[0] == "L" else s[6]))
                continue
        out.append(s)
    return out


out = []
for P in sorted(loops, key=lambda P: -abs(area(P))):
    a = area(P)
    st, segs = segment(P)
    print(f"loop  n{len(P)}  area {a:+.3f}  start {st}")
    for s in segs:
        if s[0] == "L":
            print(f"   L -> {s[1]}")
        else:
            print(f"   A c{s[1]} R{s[4]} -> {s[2]} dir{s[3]:+d}  res {s[5]} chords {s[6]}")
    out.append([st, [list(s[:4]) if s[0] == "A" else list(s) for s in segs]])
print("JSON", json.dumps(out))
