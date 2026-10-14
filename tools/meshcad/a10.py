# Eye Adaptor: unrolled cylinder sections r = R (theta in deg vs z) to show the finger outlines.
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, sys.argv[2]); from stlmesh import load
T, N, A = load(sys.argv[1])
def cylsec(R):
    s = np.hypot(T[:,:,0], T[:,:,1]) - R; out = []
    for tri, sv in zip(T, s):
        pts = []
        for i in range(3):
            j = (i+1) % 3
            if (sv[i] > 0) != (sv[j] > 0):
                t = sv[i]/(sv[i]-sv[j]); pts.append(tri[i] + t*(tri[j]-tri[i]))
        if len(pts) == 2: out.append(pts)
    return np.array(out)
Rs = [9.0, 10.3, 11.0, 11.6, 11.9, 12.1]
fig, ax = plt.subplots(len(Rs), 1, figsize=(18, 3.2*len(Rs)))
for a, R in zip(ax, Rs):
    S = cylsec(R)
    for p, q in S:
        t0, t1 = np.degrees(np.arctan2(p[1], p[0])), np.degrees(np.arctan2(q[1], q[0]))
        if abs(t0 - t1) > 180: continue
        a.plot([t0, t1], [p[2], q[2]], "k-", lw=0.8)
    a.set_xlim(-180, 180); a.set_ylim(-7, 4); a.set_xticks(range(-180, 181, 10)); a.grid(alpha=.3)
    a.set_title(f"unrolled section r = {R}")
plt.tight_layout(); plt.savefig(sys.argv[3], dpi=70); print("ok")
