import sys; sys.path.insert(0, sys.argv[2])
from stlmesh import load, section; import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
T,N,A = load(sys.argv[1]); out = sys.argv[3]
zs = [-6.0,-4.9,-4.0,-3.0,-2.0,-1.0,-0.2,0.34,1.0,2.0,3.0,3.4]
fig, ax = plt.subplots(3,4, figsize=(14,10.5))
for a,z in zip(ax.flat, zs):
    seg = section(T,2,z)
    if len(seg): a.add_collection(LineCollection(seg[:,:,:2], lw=0.8, color="k"))
    a.set_xlim(-12.5,12.5); a.set_ylim(-12.5,12.5); a.set_aspect("equal"); a.grid(alpha=.3)
    a.set_title(f"z = {z}"); a.set_xticks(range(-12,13,4)); a.set_yticks(range(-12,13,4))
plt.tight_layout(); plt.savefig(out+"_z.png", dpi=60)
fig, ax = plt.subplots(2,3, figsize=(15,7))
for a,(axis,c) in zip(ax.flat, [(1,0.0),(1,-2.0),(1,5.0),(0,0.0),(0,6.0),(0,-6.0)]):
    seg = section(T,axis,c); keep = [0,1,2]; keep.remove(axis)
    if len(seg): a.add_collection(LineCollection(seg[:,:,keep], lw=0.8, color="k"))
    a.set_xlim(-12.5,12.5); a.set_ylim(-7.5,4.5); a.set_aspect("equal"); a.grid(alpha=.3)
    a.set_title(f"{'xyz'[axis]} = {c}  (horizontal {'xyz'[keep[0]]}, vertical z)")
plt.tight_layout(); plt.savefig(out+"_v.png", dpi=60)
