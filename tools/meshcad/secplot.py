"""Plot plane sections of an STL on a grid, several levels per image, for reading a part's structure.

usage: secplot.py stl toolsdir out.png axis level [level ...]
Each panel shows the section at that level (blue) over the cap outlines AT that exact level if any (none here),
with 1 mm minor / 5 mm major grid in the plane's (u, v): x->(y,z), y->(x,z), z->(x,y).
"""
import sys, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

sys.path.insert(0, sys.argv[2])
from stlmesh import load

T = load(sys.argv[1])[0]
ax = int(sys.argv[4])
levels = [float(v) for v in sys.argv[5:]]
uv = [i for i in range(3) if i != ax]
lo, hi = T.reshape(-1, 3).min(0)[uv], T.reshape(-1, 3).max(0)[uv]
n = len(levels)
cols = min(n, 3)
rows = math.ceil(n / cols)
span = hi - lo
w = 5.0 * span[0] / max(span)
fig, axs = plt.subplots(rows, cols, figsize=(cols * max(w, 3.2) + 0.5, rows * 5.0 * span[1] / max(span) + 0.8),
                        dpi=80, squeeze=False)
for k, lv in enumerate(levels):
    a = axs[k // cols][k % cols]
    h = T[:, :, ax] - lv
    segs = []
    for t, s in zip(T, h):
        if (s > 0).all() or (s < 0).all():
            continue
        pts = []
        for i in range(3):
            j = (i + 1) % 3
            if (s[i] > 0) != (s[j] > 0):
                f = (lv - t[i][ax]) / (t[j][ax] - t[i][ax])
                pts.append((t[i] + f * (t[j] - t[i]))[uv])
        if len(pts) == 2:
            segs.append(pts)
    a.add_collection(LineCollection(segs, colors="tab:blue", linewidths=1.2))
    a.set_xlim(lo[0] - 1, hi[0] + 1); a.set_ylim(lo[1] - 1, hi[1] + 1)
    a.set_aspect("equal")
    a.set_xticks(np.arange(math.floor(lo[0] / 5) * 5, hi[0] + 5, 5))
    a.set_yticks(np.arange(math.floor(lo[1] / 5) * 5, hi[1] + 5, 5))
    a.set_xticks(np.arange(math.floor(lo[0]), hi[0] + 1, 1), minor=True)
    a.set_yticks(np.arange(math.floor(lo[1]), hi[1] + 1, 1), minor=True)
    a.grid(which="major", lw=0.6, color="0.6"); a.grid(which="minor", lw=0.3, color="0.88")
    a.tick_params(labelsize=7)
    a.set_title(f"{'xyz'[ax]} = {lv:g}   ({'xyz'[uv[0]]} across, {'xyz'[uv[1]]} up)", fontsize=9)
for k in range(n, rows * cols):
    axs[k // cols][k % cols].axis("off")
plt.tight_layout()
plt.savefig(sys.argv[3])
