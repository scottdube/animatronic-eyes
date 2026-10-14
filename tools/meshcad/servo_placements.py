# The six SG90s and their horns in "EyeMech assembly": fitted in Complete Model.stl, written into
# hardware/native/placements.json (replacing any earlier SG90 rows) for assembly_native.py.
# usage: uv run --no-project --with numpy python -I servo_placements.py "Complete Model.stl" toolsdir placements.json
#
# Servo frame (specs/sg90.py): Z up the shaft, origin on the shaft axis at the case top, +Y from the case centre to
# the shaft. Read off each copy's geometry, not fitted point to point: the right-hand servos and horns are MIRRORED
# copies with their own triangle order, so only the left two and the pan/tilt pair would take an ordered fit.
#   Z      from the lower case's centre toward the tab section's far end (the spline)
#   shaft  centroid of the top 0.25 mm of the spline (its rings are concentric)
#   origin 6.7 above the tab section's underside (2.5 tab plate + 4.2 upper case)
# Horn angle: about the servo's Z, 0 = arms along Y, from the 14.45 hole ring. Both arms carry Ø1.2 holes at 4.45 ..
# 14.45, so the horn is symmetric and only the angle mod 180 means anything.
# The Complete Model is a pose, not a closed mechanism (docs/TRAPS.md), so a horn is turned to close its linkage where
# the model leaves it open: CLOSE below names the coupler hole that horn hole must meet.
import sys, json, numpy as np
sys.path.insert(0, sys.argv[2]); import stlmesh

CM2AS = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # assembly (x, y, z) = (x_cm, z_cm, -y_cm)
# PCA9685 channel (firmware/EyeMech_PS4: 0 lex, 1 ley, 2 uplid, 3 lolid, 4 altuplid, 5 altlolid) and what it drives,
# keyed by the shaft's assembly (x, z) rounded: front row (z 41) = top lids, back row (z 54) = bottom lids, by the
# lid links' servo-end holes (each sits on its row's horn at r 14.45).
NAMES = {(-5, 54): "3 Bottom Left Lid", (-5, 41): "2 Top Left Lid", (41, 41): "1 Tilt", (37, 0): "0 Pan",
         (80, 54): "5 Bottom Right Lid", (80, 41): "4 Top Right Lid"}
# horn -> (coupler occurrence, its servo-end hole in the coupler's STL frame, horn hole radius): turn the horn so that
# hole lands on it. The right links are not in the Complete Model (placements.json mirrors the left ones), and its
# right horns sit at +-20 deg, 6.7 and 7.1 mm off them; the Y-Arm was moved 1.2 mm onto its Sub Base pin.
CLOSE = {"4 Top Right Lid": ("Top Lid Link R", (-15.435, 13.6053, 36.3006), 14.45),
         "5 Bottom Right Lid": ("Bottom Lid Link R", (-15.435, -13.5518, 49.3006), 14.45),
         "1 Tilt": ("Y-Arm", (1.5, 10.186, 34.0626), 10.45)}
# every coupler's servo end, for the closure report
ENDS = {"Top Lid Link L": (-15.435, 13.6053, 36.3006), "Top Lid Link R": (-15.435, 13.6053, 36.3006),
        "Bottom Lid Link L": (-15.435, -13.5518, 49.3006), "Bottom Lid Link R": (-15.435, -13.5518, 49.3006),
        "Y-Arm": (1.5, 10.186, 34.0626), "Three-Point Connector": (37.4998, 6.1, 14.4493)}

T, N, A = stlmesh.load(sys.argv[1])
V = np.round(T.reshape(-1, 3), 4)
u, inv = np.unique(V, axis=0, return_inverse=True); inv = inv.reshape(-1, 3)
par = np.arange(len(u))
def find(a):
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a
for a, b, c in inv:
    ra, rb, rc = find(a), find(b), find(c); par[rb] = ra; par[find(rc)] = ra
roots = np.array([find(i) for i in range(len(u))]); tr = roots[inv[:, 0]]
comps = [T[tr == r].reshape(-1, 3) for r in np.unique(tr)]
bodies = [c for c in comps if len(c) == 1340 * 3]          # lower case
tops = [c for c in comps if len(c) in (4066 * 3, 3916 * 3)]   # tab section, tower and spline
horns = [c for c in comps if len(c) == 2100 * 3]
assert (len(bodies), len(tops), len(horns)) == (6, 6, 6)

servos = []
for B in bodies:
    bc = (B.min(0) + B.max(0)) / 2
    P = min(tops, key=lambda t: np.linalg.norm(t.mean(0) - bc))
    pc = (P.min(0) + P.max(0)) / 2
    k = np.argmax(np.abs(pc - bc)); z = np.zeros(3); z[k] = np.sign(pc[k] - bc[k])
    s = P @ z
    sh = P[s > s.max() - 0.25].mean(0); sh -= (sh @ z) * z
    o = sh + (s.min() + 6.7) * z
    y = sh - (bc - (bc @ z) * z); y /= np.linalg.norm(y)
    R = np.column_stack([np.cross(y, z), y, z])            # servo frame -> CM
    Ra, oa = CM2AS @ R, CM2AS @ o
    servos.append(dict(name=NAMES[(round(oa[0]), round(oa[2]))], R=Ra, o=oa, Rcm=R, ocm=o, tip=s.max() - s.min() - 6.7))
for H in horns:
    sv = min(servos, key=lambda sv: np.linalg.norm(H.mean(0) - sv["ocm"] - 7.35 * sv["Rcm"][:, 2]))
    L = (H - sv["ocm"]) @ sv["Rcm"]
    assert abs(L[:, 2].min() - 5.45) < 1e-3 and abs(L[:, 2].max() - 9.25) < 1e-3, sv["name"]
    best = max(((np.abs(np.linalg.norm(L[:, :2] - 14.45 * np.array([-np.sin(a), np.cos(a)]), axis=1) - 0.6) < 0.02).sum(), a)
               for a in np.radians(np.arange(0, 180, 0.25)))
    c0 = 14.45 * np.array([-np.sin(best[1]), np.cos(best[1])])
    hc = L[np.abs(np.linalg.norm(L[:, :2] - c0, axis=1) - 0.6) < 0.05][:, :2].mean(0)
    sv["horn_cm"] = float(np.degrees(np.arctan2(-hc[0], hc[1])))

place = {p["occurrence"]: np.array(p["matrix"]) for p in json.load(open(sys.argv[3]))}
end = lambda n, p: place[n][:3, :3] @ np.array(p) + place[n][:3, 3]
for sv in servos:
    sv["horn"], sv["why"] = sv["horn_cm"], "as in Complete Model"
    if sv["name"] in CLOSE:
        n, p, r = CLOSE[sv["name"]]
        L = sv["R"].T @ (end(n, p) - sv["o"])
        a = np.degrees(np.arctan2(-L[0], L[1]))
        sv["horn"] = sv["horn_cm"] + (a - sv["horn_cm"] + 90) % 180 - 90     # nearest turn: the horn is symmetric
        sv["why"] = "turned %+.2f deg from the Complete Model's %.2f to meet %s (hole radius %.3f, horn hole %.2f)" % (
            sv["horn"] - sv["horn_cm"], sv["horn_cm"], n, np.hypot(L[0], L[1]), r)

def horn_holes(sv):
    a = np.radians(sv["horn"]); d = np.array([-np.sin(a), np.cos(a), 0])
    return [sv["o"] + sv["R"] @ (h * d) for h in np.r_[np.arange(4.45, 15, 2), -np.arange(4.45, 15, 2)]]
for n, p in ENDS.items():
    q = end(n, p)
    d, s = min((np.linalg.norm((h - q) - ((h - q) @ sv["R"][:, 2]) * sv["R"][:, 2]), sv["name"])
               for sv in servos if np.linalg.norm(sv["o"] - q) < 30 for h in horn_holes(sv))
    print("  closure %-22s %.4f mm off the nearest hole of horn %s (across the shaft axis)" % (n, d, s))

rows = [e for e in json.load(open(sys.argv[3])) if e["part"] not in ("SG90", "SG90 Horn")]
def row(occ, part, R, o, note):
    M = np.eye(4); M[:3, :3], M[:3, 3] = R, o
    return dict(occurrence=occ, part=part, kind="servo", matrix=np.round(M, 7).tolist(),
                stl="from-complete-model/%s.stl" % part, note=note)
for sv in sorted(servos, key=lambda s: s["name"]):
    a = np.radians(sv["horn"]); Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rows.append(row("Servo " + sv["name"], "SG90", sv["R"], sv["o"], "shaft along %s" % np.round(sv["R"][:, 2], 4).tolist()))
    rows.append(row("Horn " + sv["name"], "SG90 Horn", sv["R"] @ Rz, sv["o"], "%.4f deg about the shaft, %s" % (
        sv["horn"], sv["why"])))
    print("  %-22s shaft (%.4f, %.4f, %.4f) along %s, spline %.3f; horn %.4f deg (%s)" % (
        sv["name"], *sv["o"], np.round(sv["R"][:, 2], 4).tolist(), sv["tip"], sv["horn"], sv["why"]))
json.dump(rows, open(sys.argv[3], "w"), indent=1)
print(len(rows), "rows ->", sys.argv[3])
