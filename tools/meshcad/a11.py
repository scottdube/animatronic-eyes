# Eye Adaptor: top surfaces of the finger walls. Print up-facing triangles (nz>0.02) on the
# wall ring (10.6<r<11.75) with their normal, so we can tell X-, Y- or radial extrusions apart.
import sys, numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load
T, N, A = load(sys.argv[1])
C = T.mean(1); r = np.hypot(C[:,0], C[:,1]); th = np.degrees(np.arctan2(C[:,1], C[:,0]))
lo, hi = float(sys.argv[3]), float(sys.argv[4])
m = (r > 10.6) & (r < 11.75) & (N[:,2] > 0.02) & (th > lo) & (th < hi) & (C[:,2] > -6)
for i in np.argsort(th[m]):
    j = np.where(m)[0][i]; P = T[j]
    print(f"th{th[j]:+7.2f} n({N[j,0]:+.3f},{N[j,1]:+.3f},{N[j,2]:+.3f}) A{A[j]:.3f} "
          + " ".join(f"({p[0]:+.3f},{p[1]:+.3f},{p[2]:+.3f})" for p in P))
