import sys; sys.path.insert(0, sys.argv[2])
from stlmesh import load; import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
T,N,A = load(sys.argv[1]); out = sys.argv[3]
views = [(35,-60),(35,30),(35,120),(35,210),(-35,-60),(-35,120)]
fig = plt.figure(figsize=(15,10))
L = np.array([0.4,-0.5,0.8]); L /= np.linalg.norm(L)
for k,(el,az) in enumerate(views):
    ax = fig.add_subplot(2,3,k+1, projection="3d")
    # light fixed relative to the camera
    e, a = np.radians(el), np.radians(az)
    cam = np.array([np.cos(e)*np.cos(a), np.cos(e)*np.sin(a), np.sin(e)])
    sh = np.clip(np.abs(N@ (cam*0.7 + np.array([0,0,0.3]))), 0.15, 1)
    pc = Poly3DCollection(T, facecolors=plt.cm.Greys(0.25+0.6*sh), edgecolor="none")
    ax.add_collection3d(pc)
    ax.set_xlim(-12,12); ax.set_ylim(-12,12); ax.set_zlim(-9,5); ax.set_box_aspect((24,24,14))
    ax.view_init(el, az); ax.set_title(f"elev {el} azim {az}"); ax.set_xlabel("x"); ax.set_ylabel("y")
plt.tight_layout(); plt.savefig(out, dpi=55)
