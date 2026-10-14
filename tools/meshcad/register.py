"""Place every kit part STL in Complete Model.stl: rigid transform from the part's own frame to each shell it matches.

usage: register.py kit-stl-dir toolsdir [out.json]

Complete Model is the parts rotated +90 deg about X, but not every part STL sits where the model has it (the Y-Arm
is 45 mm off in x, the lids are posed), so each copy is registered: shells matched by volume and sorted extents, a
start from the solid's centroid and inertia axes (all sign flips tried), then point-to-point ICP of the part's
vertices onto a dense sample of the shell's surface. Transforms are reported in the PARTS frame (Rx(-90) applied to
the model first), as 4x4 row-major mm, which is what the assembly inserts at.
"""
import sys, os, glob, json, itertools
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, sys.argv[2])
from stlmesh import load

RXm90 = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)   # model frame -> parts frame


def shells(T):
    V = np.round(T.reshape(-1, 3), 4)
    uniq, inv = np.unique(V, axis=0, return_inverse=True)
    inv = inv.reshape(-1, 3)
    par = np.arange(len(uniq))

    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for a, b, c in inv:
        ra = f(a)
        par[f(b)] = ra
        par[f(c)] = ra
    root = np.array([f(i) for i in range(len(uniq))])
    comp = root[inv[:, 0]]
    return [T[comp == k] for k in np.unique(comp)]


def mass(T):
    """volume, centroid, inertia tensor about the centroid (solid, unit density)."""
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    d = np.einsum('ij,ij->i', a, np.cross(b, c)) / 6
    v = d.sum()
    cen = ((a + b + c) / 4 * d[:, None]).sum(0) / v
    a, b, c = a - cen, b - cen, c - cen
    # second moments of each tetra (origin=centroid, a, b, c)
    S = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            S[i, j] = (d * (2 * (a[:, i] * a[:, j] + b[:, i] * b[:, j] + c[:, i] * c[:, j]) +
                            a[:, i] * b[:, j] + b[:, i] * a[:, j] + a[:, i] * c[:, j] + c[:, i] * a[:, j] +
                            b[:, i] * c[:, j] + c[:, i] * b[:, j]) / 20).sum()
    return v, cen, S


def sample(T, step=0.25):
    pts = [T.reshape(-1, 3)]
    e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    area = np.linalg.norm(np.cross(e1, e2), axis=1) / 2
    n = np.maximum(1, (area / step ** 2).astype(int))
    idx = np.repeat(np.arange(len(T)), n)
    r1, r2 = np.random.default_rng(0).random((2, len(idx)))
    m = r1 + r2 > 1
    r1[m], r2[m] = 1 - r1[m], 1 - r2[m]
    pts.append(T[idx, 0] + r1[:, None] * e1[idx] + r2[:, None] * e2[idx])
    return np.vstack(pts)


def icp(P, tree, Q, R, t, it=60):
    for _ in range(it):
        X = P @ R.T + t
        d, j = tree.query(X)
        Y = Q[j]
        mx, my = X.mean(0), Y.mean(0)
        U, _, Wt = np.linalg.svd((X - mx).T @ (Y - my))
        D = np.diag([1, 1, np.sign(np.linalg.det(Wt.T @ U.T))])
        dR = Wt.T @ D @ U.T
        R, t = dR @ R, dR @ (t - mx) + my
    d, _ = tree.query(P @ R.T + t)
    return R, t, d


def main():
    kit = sys.argv[1]
    M = load(os.path.join(kit, "Complete Model.stl"))[0] @ RXm90.T
    S = [(s, *mass(s)) for s in shells(M)]
    out = {}
    for p in sorted(glob.glob(os.path.join(kit, "*.stl"))):
        name = os.path.basename(p)[:-4]
        if name == "Complete Model":
            continue
        T = load(p)[0]
        v, c, I = mass(T)
        ext = np.sort(np.ptp(T.reshape(-1, 3), 0))
        P = np.unique(T.reshape(-1, 3), axis=0)
        P = P[np.random.default_rng(1).permutation(len(P))[:4000]]
        hits = []
        for k, (s, sv, sc, sI) in enumerate(S):
            if abs(sv - v) > 0.08 * v or np.abs(np.sort(np.ptp(s.reshape(-1, 3), 0)) - ext).max() > 2.0:
                continue
            Q = sample(s)
            tree = cKDTree(Q)
            w1, E1 = np.linalg.eigh(I)
            w2, E2 = np.linalg.eigh(sI)
            best = None
            for sg in itertools.product((1, -1), repeat=3):
                R0 = E2 @ np.diag(sg) @ E1.T
                if np.linalg.det(R0) < 0:
                    continue
                for R0 in (R0, np.eye(3)):   # translation-only start too: near-symmetric parts confuse inertia
                    R, t, d = icp(P, tree, Q, R0, sc - R0 @ c)
                    if best is None or d.max() < best[2].max():
                        best = (R, t, d)
            R, t, d = best
            ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
            hits.append(dict(shell=k, vol=round(sv, 1), rot_deg=round(ang, 3), max=round(d.max(), 4),
                             mean=round(d.mean(), 4), R=np.round(R, 6).tolist(), t=np.round(t, 4).tolist()))
        out[name] = hits
        print(f"{name}  vol {v:.1f}")
        for h in hits:
            print(f"   shell {h['shell']:3d} vol {h['vol']:8.1f} rot {h['rot_deg']:8.3f} deg  t {h['t']}  "
                  f"max {h['max']:.4f} mean {h['mean']:.4f}")
    if len(sys.argv) > 3:
        json.dump(out, open(sys.argv[3], "w"), indent=1)


main()
