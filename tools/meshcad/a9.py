# Eye Adaptor: segment the snap-finger region into planar faces (coplanar triangle groups)
# and print each with area, normal, offset and extents, plus cylindrical extents (r, theta).
import sys, numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load
T, N, A = load(sys.argv[1])
C = T.mean(1); r = np.hypot(C[:,0], C[:,1])
sel = (r > 8.0) | (np.abs(C[:,0]) > 9.0)
T, N, A, C = T[sel], N[sel], A[sel], C[sel]
d = (N * C).sum(1)
used = np.zeros(len(T), bool); groups = []
for i in np.argsort(-A):
    if used[i]: continue
    m = (~used) & ((N @ N[i]) > 0.99995) & (np.abs(d - d[i]) < 0.005)
    used |= m; groups.append(m)
rows = []
for m in groups:
    a = A[m].sum()
    if a < 0.05: continue
    P = T[m].reshape(-1,3); n = (N[m]*A[m,None]).sum(0); n /= np.linalg.norm(n)
    th = np.degrees(np.arctan2(P[:,1], P[:,0])); rr = np.hypot(P[:,0], P[:,1])
    rows.append((a, n, (n*P).sum(1).mean(), P.min(0), P.max(0), rr.min(), rr.max(), th.min(), th.max(), m.sum()))
for a,n,dd,lo,hi,r0,r1,t0,t1,k in sorted(rows, key=lambda x:(round(x[1][2],2), -x[0])):
    print(f"A{a:6.2f} k{k:3d} n({n[0]:+.3f},{n[1]:+.3f},{n[2]:+.3f}) d{dd:+8.3f}  x[{lo[0]:+7.2f},{hi[0]:+7.2f}] y[{lo[1]:+7.2f},{hi[1]:+7.2f}] z[{lo[2]:+6.2f},{hi[2]:+6.2f}] r[{r0:5.2f},{r1:5.2f}] th[{t0:+7.1f},{t1:+7.1f}]")
print("curved leftovers:", (~np.any(np.array(groups),0)).sum() if groups else 0)
