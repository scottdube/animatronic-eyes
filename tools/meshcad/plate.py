# Is this mesh a plate (a 2D profile extruded along one axis)? Classify every triangle by its normal
# against the axis: cap (|n.a| > 0.9999), wall (|n.a| < 1e-3) or other. Print the cap levels with their
# areas, and the 'other' triangles grouped by plane, since those are the non-prismatic features.
# usage: plate.py stl toolsdir axis(0|1|2)
import sys, numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load
T, N, A = load(sys.argv[1]); ax = int(sys.argv[3])
na = N[:, ax]
cap, wall = np.abs(na) > 0.9999, np.abs(na) < 1e-3
other = ~cap & ~wall
print(f"tris {len(T)}  cap {cap.sum()}  wall {wall.sum()}  other {other.sum()}  (area other {A[other].sum():.2f})")
lv = np.round(T[cap][:, :, ax].mean(1), 3)
for v in np.unique(lv):
    m = lv == v
    s = np.sign(na[cap][m]).mean()
    print(f"  cap at {v:+.3f}  area {A[cap][m].sum():8.2f}  facing {s:+.0f}")
if other.any():
    C = T[other].mean(1); n = N[other]; d = (n * C).sum(1); a = A[other]
    used = np.zeros(len(C), bool)
    for i in np.argsort(-a):
        if used[i]: continue
        m = (~used) & ((n @ n[i]) > 0.9999) & (np.abs(d - d[i]) < 0.005)
        used |= m
        P = T[other][m].reshape(-1, 3)
        print(f"  other A{a[m].sum():7.3f} k{m.sum():4d} n({n[i][0]:+.3f},{n[i][1]:+.3f},{n[i][2]:+.3f}) d{d[i]:+8.3f} "
              f"lo {np.round(P.min(0), 3)} hi {np.round(P.max(0), 3)}")
