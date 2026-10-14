import numpy as np, struct
def load(p):
    d = open(p, "rb").read(); n = struct.unpack("<I", d[80:84])[0]
    a = np.frombuffer(d[84:84+n*50], dtype=np.dtype([("n","<3f4"),("v","<9f4"),("a","<u2")]))
    T = a["v"].reshape(-1,3,3).astype(float)
    N = np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0]); A = np.linalg.norm(N,axis=1)/2
    N = N/np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-12)
    return T, N, A

def section(T, axis, c):
    """Segments where plane x[axis]=c cuts the triangles; returns (k,2,3)."""
    s = T[:,:,axis] - c
    out = []
    for tri, sv in zip(T, s):
        pts = []
        for i in range(3):
            j = (i+1) % 3
            if (sv[i] > 0) != (sv[j] > 0):
                t = sv[i]/(sv[i]-sv[j]); pts.append(tri[i] + t*(tri[j]-tri[i]))
        if len(pts) == 2: out.append(pts)
    return np.array(out)

def zhits(T, x, y):
    """All z where the vertical line at (x,y) crosses the mesh, sorted."""
    a,b,c = T[:,0,:2],T[:,1,:2],T[:,2,:2]; p = np.array([x,y])
    v0, v1, v2 = c-a, b-a, p-a
    d00=(v0*v0).sum(1); d01=(v0*v1).sum(1); d11=(v1*v1).sum(1); d02=(v0*v2).sum(1); d12=(v1*v2).sum(1)
    den = d00*d11-d01*d01; ok = np.abs(den) > 1e-12
    u = np.where(ok,(d11*d02-d01*d12)/np.where(ok,den,1),-1); v = np.where(ok,(d00*d12-d01*d02)/np.where(ok,den,1),-1)
    m = ok & (u>=-1e-9) & (v>=-1e-9) & (u+v<=1+1e-9)
    z = T[m,0,2] + u[m]*(T[m,2,2]-T[m,0,2]) + v[m]*(T[m,1,2]-T[m,0,2])
    return np.unique(np.round(z,3))

def circfit(P2):
    x,y = P2[:,0],P2[:,1]
    M = np.c_[2*x,2*y,np.ones(len(x))]; b = x*x+y*y
    (cx,cy,c),*_ = np.linalg.lstsq(M,b,rcond=None); R = np.sqrt(c+cx*cx+cy*cy)
    res = np.hypot(x-cx,y-cy)-R
    return cx,cy,R,np.abs(res).max(),len(x)

def section_plane(T, n, c):
    """Segments where the plane n.x = c cuts the triangles; returns (k,2,3)."""
    n = np.asarray(n, float); s = T @ n - c
    out = []
    for tri, sv in zip(T, s):
        pts = []
        for i in range(3):
            j = (i+1) % 3
            if (sv[i] > 0) != (sv[j] > 0):
                t = sv[i]/(sv[i]-sv[j]); pts.append(tri[i] + t*(tri[j]-tri[i]))
        if len(pts) == 2: out.append(pts)
    return np.array(out)
