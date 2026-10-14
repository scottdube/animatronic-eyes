# Column-thickness comparison of two closed meshes: for a grid of vertical lines, total material
# length along each line in A and in B. Prints the volume each implies and where they differ most.
# Catches what a vertex-to-body check cannot: material one side has that the other lacks.
# usage: thickdiff.py A.stl B.stl toolsdir [step_mm] [min_diff_mm] [axis]
# axis (0|1|2, default 2) is the column direction: give a plate's extrusion axis so the grid covers its profile.
import sys
sys.path.insert(0, sys.argv[3])
import numpy as np
from stlmesh import load


def thickness(T, xs, ys):
    lo, hi = T[:, :, :2].min(1), T[:, :, :2].max(1)
    out = np.full((len(ys), len(xs)), np.nan)
    for j, y in enumerate(ys):
        band = T[(lo[:, 1] <= y) & (hi[:, 1] >= y)]
        blo, bhi = band[:, :, 0].min(1), band[:, :, 0].max(1)
        for i, x in enumerate(xs):
            t = band[(blo <= x) & (bhi >= x)]
            if not len(t):
                out[j, i] = 0.0
                continue
            a, b, c = t[:, 0, :2], t[:, 1, :2], t[:, 2, :2]
            v0, v1, v2 = c - a, b - a, np.array([x, y]) - a
            d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
            d02 = (v0 * v2).sum(1); d12 = (v1 * v2).sum(1)
            den = d00 * d11 - d01 * d01
            ok = np.abs(den) > 1e-12
            den = np.where(ok, den, 1)
            u = (d11 * d02 - d01 * d12) / den; v = (d00 * d12 - d01 * d02) / den
            m = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
            z = np.sort(t[m, 0, 2] + u[m] * (t[m, 2, 2] - t[m, 0, 2]) + v[m] * (t[m, 1, 2] - t[m, 0, 2]))
            out[j, i] = (z[1::2] - z[0::2]).sum() if len(z) % 2 == 0 else np.nan
    return out


A, B = load(sys.argv[1])[0], load(sys.argv[2])[0]
ax = int(sys.argv[6]) if len(sys.argv) > 6 else 2
perm = [(ax + 1) % 3, (ax + 2) % 3, ax]  # cyclic, so the column axis becomes z
A, B = A[:, :, perm], B[:, :, perm]
step = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
mind = float(sys.argv[5]) if len(sys.argv) > 5 else 0.05
lo = min(A[:, :, :2].min(), B[:, :, :2].min()) - step
hi = max(A[:, :, :2].max(), B[:, :, :2].max()) + step
g = np.arange(lo, hi, step) + 0.0137 * step  # off-grid so lines miss shared edges
ta, tb = thickness(A, g, g), thickness(B, g, g)
bad = np.isnan(ta) | np.isnan(tb)
d = np.where(bad, 0, tb - ta)
print(f"grid {len(g)}^2 step {step}  odd-parity columns {bad.sum()}")
print(f"volume A {np.nansum(ta) * step * step:.2f} mm3  B {np.nansum(tb) * step * step:.2f} mm3  "
      f"B-A {d.sum() * step * step:+.2f} mm3")
print(f"columns |B-A| > {mind}: {(np.abs(d) > mind).sum()}")
for sign, name in ((1, "B thicker"), (-1, "A thicker")):
    m = sign * d > mind
    if not m.any():
        continue
    J, I = np.nonzero(m)
    print(f"{name}: {m.sum()} cols, {sign * d[m].sum() * step * step:.2f} mm3, "
          f"x {g[I].min():.2f}..{g[I].max():.2f} y {g[J].min():.2f}..{g[J].max():.2f}")
    order = np.argsort(-sign * d[m])[:12]
    for k in order:
        print(f"   ({g[I[k]]:7.3f}, {g[J[k]]:7.3f})  A {ta[J[k], I[k]]:.3f}  B {tb[J[k], I[k]]:.3f}  r {np.hypot(g[I[k]], g[J[k]]):.3f}")

# Columns that graze a vertical wall differ by whole wall heights between meshes and swamp the sum.
# Drop any column whose neighbour's thickness differs by > 0.3 in either mesh, then cluster by 1 mm cell.
def edge(t):
    t = np.nan_to_num(t); e = np.zeros_like(t, bool)
    for ax in (0, 1):
        for s in (1, -1):
            e |= np.abs(t - np.roll(t, s, ax)) > 0.3
    return e

dk = np.where(edge(ta) | edge(tb), 0, d)
print(f"off-wall B-A {dk.sum() * step * step:+.2f} mm3 (wall-grazing columns {(d - dk).sum() * step * step:+.2f})")
cells = {}
for j, i in zip(*np.nonzero(np.abs(dk) > 0.02)):
    k = (round(g[i]), round(g[j])); cells[k] = cells.get(k, 0) + dk[j, i] * step * step
for k, v in sorted(cells.items(), key=lambda kv: -abs(kv[1]))[:15]:
    print(f"   cell x {k[0]:+d} y {k[1]:+d}: {v:+.3f} mm3")
