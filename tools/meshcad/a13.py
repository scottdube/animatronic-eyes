# Eye Adaptor: (r, z) profile of revolved surfaces: vertices in a theta window and box, rounded and deduped.
import sys, numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load
T, N, A = load(sys.argv[1]); t0, t1, r0, r1, z0, z1 = [float(v) for v in sys.argv[3].split(",")]
V = np.unique(np.round(T.reshape(-1,3), 4), axis=0)
r = np.hypot(V[:,0], V[:,1]); th = np.degrees(np.arctan2(V[:,1], V[:,0]))
m = (th>t0)&(th<t1)&(r>r0)&(r<r1)&(V[:,2]>z0)&(V[:,2]<z1)
P = np.unique(np.round(np.c_[r[m], V[m,2]], 3), axis=0)
for p in P[np.lexsort((P[:,0], P[:,1]))]: print(f"{p[0]:8.3f} {p[1]:+8.3f}")
