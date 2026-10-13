import sys; sys.path.insert(0, sys.argv[2])
from stlmesh import load, circfit; import numpy as np
T,N,A = load(sys.argv[1])
def verts(pred_tri, pred_v):
    P = T[pred_tri].reshape(-1,3); P = np.unique(np.round(P,4),axis=0)
    return P[pred_v(P)]
ny0 = np.abs(N[:,1]) < 0.02
ymid = lambda lo,hi: (T[:,:,1].min(1) >= lo-1e-3) & (T[:,:,1].max(1) <= hi+1e-3)
fits = {
 "R lug top (y 1..-3.1, x>3.5, z>-1.95)": verts(ny0 & (N[:,2]>0.05) & ymid(-3.1,1), lambda P:(P[:,0]>3.55)&(P[:,2]>-1.96)&(P[:,1]>0.9)),
 "L lug top": verts(ny0 & (N[:,2]>0.05) & ymid(-3.1,1), lambda P:(P[:,0]<-3.55)&(P[:,2]>-1.96)&(P[:,1]>0.9)),
 "R lug hole": verts(ny0 & ymid(-3.1,1), lambda P:(P[:,0]>3.7)&(P[:,0]<8.3)&(P[:,2]>-4)&(P[:,2]<0)&(np.hypot(P[:,0]-6,P[:,2]+2)<2)&(P[:,1]>0.9)),
 "L lug hole": verts(ny0 & ymid(-3.1,1), lambda P:(P[:,0]<-3.7)&(P[:,0]>-8.3)&(P[:,2]>-4)&(P[:,2]<0)&(np.hypot(P[:,0]+6,P[:,2]+2)<2)&(P[:,1]>0.9)),
 "R gusset top": verts(ny0 & (N[:,2]>0.05) & ymid(-7.7,-3.0), lambda P:(P[:,0]>3.6)&(P[:,0]<8)&(P[:,2]>-1.5)&(np.abs(P[:,1]+3.5)<0.6)),
 "L gusset top": verts(ny0 & (N[:,2]>0.05) & ymid(-7.7,-3.0), lambda P:(P[:,0]<-3.6)&(P[:,0]>-8)&(P[:,2]>-1.5)&(np.abs(P[:,1]+3.5)<0.6)),
 "center lug top": verts(ny0 & (N[:,2]>0.05), lambda P:(np.abs(P[:,0])<3.5)&(P[:,2]>0.5)&(np.abs(P[:,1]+3.0)<0.05)),
 "center hole": verts(ny0, lambda P:(np.hypot(P[:,0],P[:,2])<1.8)&(np.abs(P[:,1]+3.0)<0.05)),
}
for k,P in fits.items():
    if len(P)<3: print(k,"too few",len(P)); continue
    cx,cz,R,res,n = circfit(P[:,[0,2]])
    print(f"{k:42s} centre x={cx:+.3f} z={cz:+.3f} R={R:.3f} (Ø{2*R:.3f}) maxres={res:.3f} n={n} y[{P[:,1].min():.2f},{P[:,1].max():.2f}]")
