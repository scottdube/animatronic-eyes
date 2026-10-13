import sys; sys.path.insert(0, sys.argv[2])
from stlmesh import load, zhits; import numpy as np
T,N,A = load(sys.argv[1])
xs = np.arange(3.0, 9.01, 0.5); ys = np.arange(1.0, -8.51, -0.5)
print("top z;  rows y, cols x =", " ".join(f"{x:5.1f}" for x in xs))
for y in ys:
    row = []
    for x in xs:
        z = zhits(T,x+1e-4,y+1e-4); row.append(f"{z.max():5.2f}" if len(z) else "   - ")
    print(f"y={y:5.1f}  " + " ".join(row))
