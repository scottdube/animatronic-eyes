# Rotate an STL about a coordinate axis through the origin, so a part whose faces sit at an angle (the eyelids'
# lips, 20 deg about the pivot) can be decoded with the axis-aligned tools. Right-hand rule: +deg about x takes
# +y toward +z. usage: rotstl.py in.stl toolsdir axis deg out.stl
import sys, struct, math
import numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load

T, N, A = load(sys.argv[1]); ax = "xyz".index(sys.argv[3]); a = math.radians(float(sys.argv[4]))
c, s = math.cos(a), math.sin(a)
i, j = [k for k in range(3) if k != ax]
R = np.eye(3); R[i, i], R[i, j], R[j, i], R[j, j] = c, -s, s, c
if ax == 1:      # about y the cyclic order is (z, x)
    R = R.T
T2 = T @ R.T
N2 = np.cross(T2[:, 1] - T2[:, 0], T2[:, 2] - T2[:, 0])
N2 /= np.linalg.norm(N2, axis=1)[:, None]
with open(sys.argv[5], "wb") as f:
    f.write(b"rotstl".ljust(80, b" ") + struct.pack("<I", len(T2)))
    for n, t in zip(N2, T2):
        f.write(struct.pack("<12fH", *n, *t.ravel(), 0))
