import sys; sys.path.insert(0, sys.argv[2])
from stlmesh import load; import numpy as np
T,N,A = load(sys.argv[1])
key = np.round(N,3); d = np.round((N*T[:,0]).sum(1),2)
g = {}
for i,(k,dd) in enumerate(zip(map(tuple,key), d)): g.setdefault((k,dd),[]).append(i)
rows = []
for (k,dd),idx in g.items():
    a = A[idx].sum()
    if a < 0.4: continue
    P = T[idx].reshape(-1,3)
    rows.append((a,k,dd,P.min(0),P.max(0),len(idx)))
rows.sort(key=lambda r:(r[1],r[2]))
for a,k,dd,lo,hi,n in rows:
    print(f"n=({k[0]:+.3f},{k[1]:+.3f},{k[2]:+.3f}) d={dd:+7.2f} A={a:6.2f} x[{lo[0]:+6.2f},{hi[0]:+6.2f}] y[{lo[1]:+6.2f},{hi[1]:+6.2f}] z[{lo[2]:+6.2f},{hi[2]:+6.2f}] t={n}")
print("planar area", sum(r[0] for r in rows).round(1), "of", A.sum().round(1))
