import sys; sys.path.insert(0, sys.argv[2])
from stlmesh import load, section; import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
T,N,A = load(sys.argv[1]); out = sys.argv[3]
cuts = [(1,0.5),(1,-3.5),(1,-4.5),(1,-5.5),(1,-6.5),(1,-7.5),(0,4.5),(0,6.0),(0,7.5),(0,1.0),(0,-10.5),(0,11.0)]
fig, ax = plt.subplots(4,3, figsize=(15,12))
for a,(axis,c) in zip(ax.flat, cuts):
    seg = section(T,axis,c); keep=[0,1,2]; keep.remove(axis)
    if len(seg): a.add_collection(LineCollection(seg[:,:,keep], lw=0.8, color="k"))
    a.set_xlim(-12.5,12.5); a.set_ylim(-7,4); a.set_aspect("equal"); a.grid(alpha=.4)
    a.set_xticks(range(-12,13,1), minor=True); a.set_yticks(range(-7,5,1)); a.grid(which="minor", alpha=.15)
    a.set_title(f"{'xyz'[axis]} = {c}  (horiz {'xyz'[keep[0]]})")
plt.tight_layout(); plt.savefig(out, dpi=55)
