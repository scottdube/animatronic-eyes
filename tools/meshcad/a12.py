# Eye Adaptor: (u, z) profile of an extruded top surface. axis = 0 -> extruded along X (profile y,z),
# axis = 1 -> along Y (profile x,z). Keeps up-facing triangles with |n[axis]| < 0.01 inside a box.
import sys, numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load, circfit
T, N, A = load(sys.argv[1]); ax = int(sys.argv[3]); box = [float(v) for v in sys.argv[4].split(",")]
x0,x1,y0,y1,z0,z1 = box; u = 1 - ax
C = T.mean(1)
m = (np.abs(N[:,ax]) < 0.01) & (N[:,2] > -0.999) & (C[:,0]>x0)&(C[:,0]<x1)&(C[:,1]>y0)&(C[:,1]<y1)&(C[:,2]>z0)&(C[:,2]<z1)
P = np.unique(np.round(T[m].reshape(-1,3)[:, [u,2]], 3), axis=0)
P = P[np.argsort(P[:,0])]
for p in P: print(f"{p[0]:+8.3f} {p[1]:+8.3f}")
