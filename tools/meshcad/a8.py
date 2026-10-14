import sys; sys.path.insert(0, sys.argv[2])
from stlmesh import load, section, section_plane; import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
T,N,A = load(sys.argv[1]); out = sys.argv[3]
fig, ax = plt.subplots(2,4, figsize=(16,8))
for a,z in zip(ax.flat, [-6.5,-5.5,-4.5,-3.0,-1.0,0.0,0.35,1.5]):
    seg = section(T,2,z)
    if len(seg): a.add_collection(LineCollection(seg[:,:,:2], lw=1, color="k"))
    a.set_xlim(-12.6,-8.6); a.set_ylim(-3,3); a.set_aspect("equal"); a.grid(alpha=.4)
    a.set_xticks(np.arange(-12.5,-8.4,0.5), minor=True); a.set_yticks(np.arange(-3,3.1,0.5), minor=True); a.grid(which="minor",alpha=.15)
    a.set_title(f"-X zoom, z = {z}")
plt.tight_layout(); plt.savefig(out+"_negx.png", dpi=55)
fig, ax = plt.subplots(2,4, figsize=(16,8))
for a,th in zip(ax.flat, [20,40,60,90,135,155,175,-40]):
    t = np.radians(th); d = np.array([np.cos(t), np.sin(t), 0]); n = np.array([-np.sin(t), np.cos(t), 0])
    seg = section_plane(T, n, 0.0)
    if len(seg):
        r = seg @ d; z = seg[:,:,2]; P = np.stack([r,z],-1); P = P[(P[:,:,0]>0).all(1)]
        a.add_collection(LineCollection(P, lw=1, color="k"))
    a.set_xlim(7,12.5); a.set_ylim(-7,3); a.set_aspect("equal"); a.grid(alpha=.4)
    a.set_xticks(np.arange(7,12.6,0.5), minor=True); a.set_yticks(np.arange(-7,3.1,0.5), minor=True); a.grid(which="minor",alpha=.15)
    a.set_title(f"radial section at {th} deg (horiz r)")
plt.tight_layout(); plt.savefig(out+"_rad.png", dpi=55)
