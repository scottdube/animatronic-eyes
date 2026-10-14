"""Shaded multi-view PNG of an STL, for reading a part's shape before decoding it.

usage: render.py stl toolsdir out.png [elev,azim ...]   (default: four iso views)
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

sys.path.insert(0, sys.argv[2])
from stlmesh import load

T, N, A = load(sys.argv[1])
views = [tuple(map(float, v.split(","))) for v in sys.argv[4:]] or [(30, -60), (30, 120), (-30, 30), (60, -150)]
light = np.array([0.4, -0.5, 0.75]); light /= np.linalg.norm(light)
lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
c, r = (lo + hi) / 2, (hi - lo).max() / 2
fig = plt.figure(figsize=(10, 8), dpi=90)
for i, (el, az) in enumerate(views):
    ax = fig.add_subplot(2, (len(views) + 1) // 2, i + 1, projection="3d")
    sh = 0.35 + 0.65 * np.abs(N @ light)
    ax.add_collection3d(Poly3DCollection(T, facecolors=np.c_[sh * .55, sh * .7, sh * .9], edgecolor="none"))
    for k, s in enumerate("xyz"):
        getattr(ax, f"set_{s}lim")(c[k] - r, c[k] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(el, az)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    ax.set_title(f"elev {el:g} azim {az:g}", fontsize=8)
    ax.tick_params(labelsize=6)
plt.tight_layout()
plt.savefig(sys.argv[3])
