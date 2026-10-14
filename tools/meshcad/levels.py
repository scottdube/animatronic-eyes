# Distinct vertex coordinates per axis (clustered to 1e-3), with how many vertices sit at each: a mesh's shape
# only changes at these levels, so they are where to put sections and where features start and stop.
# usage: levels.py stl toolsdir [min_count]
import sys, numpy as np
sys.path.insert(0, sys.argv[2]); from stlmesh import load
T = load(sys.argv[1])[0]
V = np.unique(np.round(T.reshape(-1, 3), 4), axis=0)
mn = int(sys.argv[3]) if len(sys.argv) > 3 else 4
for k, a in enumerate("xyz"):
    v = np.round(V[:, k], 3)
    u, c = np.unique(v, return_counts=True)
    print(a, " ".join(f"{x:g}({n})" for x, n in zip(u, c) if n >= mn))
