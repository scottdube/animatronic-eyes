import sys; sys.path.insert(0, sys.argv[2])
from stlmesh import load; import numpy as np
T,N,A = load(sys.argv[1])
P = np.unique(np.round(T.reshape(-1,3),4),axis=0)
sel = P[(np.abs(P[:,1]-1.0)<1e-3)&(P[:,0]>3.4)&(P[:,0]<8.5)&(P[:,2]>-2.1)]
sel = sel[np.argsort(np.arctan2(sel[:,2]+1.95, sel[:,0]-5.859))]
for p in sel:
    r = np.hypot(p[0]-5.859,p[2]+1.95); r2=np.hypot(p[0]-6.0,p[2]+1.95)
    print(f"x={p[0]:+.4f} z={p[2]:+.4f}  r(hole axis)={r:.3f}  r(x=6)={r2:.3f}")
