"""Assembly placements for every kit part occurrence, fitted against Complete Model.stl.

usage: placements.py kit-stl-dir toolsdir out.json

register.py found how each part sits in the model; this pins each to a clean, explainable motion and fits only the
free parameters, so the assembly carries numbers that mean something:
  identity  part STL already where the model has it (rotation < 0.04 deg, shift < 0.02 mm in register.py)
  copy+75   the right eye's copy of a part printed twice: the SAME part moved +75 mm in x. Complete Model mirrors the
            whole left eye about x = 37.5 instead, which only a mirrored print could be (the Eye Adaptor's +X/-X
            snap fingers differ, so the mirror is 3 mm off a printable copy)
  lid       rotation about the X axis through the eye centre (origin), angle fitted
  plate     X-normal plates (lid links, Y-Arm): rotation about X plus a shift in Y/Z, fitted; the X shift is the
            difference of plate mid-planes
  mirror    right-eye copy of an X-normal plate the model leaves out: the left pose reflected about x = 37.5, and the
            plate reflected about its own mid-plane first, which together are a rigid motion
  rlid      right lids: the left lid's pose, reflected about x = 37.5, applied to the right lid reflected back in Z
            (the Right Lid STLs are the Left ones reflected in Z)
Each fitted occurrence reports the max/mean distance from its part's vertices to the model shell; the model is
coarser, so ~0.3-0.4 mm is chord error, not misplacement.
"""
import sys, os, json
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, sys.argv[2])
from stlmesh import load
src = open(os.path.join(sys.argv[2], "register.py")).read().split("\ndef main")[0]
reg = {}
exec(compile(src, "register.py", "exec"), reg)

KIT = sys.argv[1]
MODEL = load(os.path.join(KIT, "Complete Model.stl"))[0] @ reg["RXm90"].T
SHELLS = reg["shells"](MODEL)
MX = np.diag([-1.0, 1, 1])


def H(R=np.eye(3), t=(0, 0, 0)):
    m = np.eye(4)
    m[:3, :3], m[:3, 3] = R, t
    return m


def Rx(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def refl_x(x0):   # reflection about the plane x = x0
    return H(MX, (2 * x0, 0, 0))


def verts(name):
    return np.unique(load(os.path.join(KIT, name + ".stl"))[0].reshape(-1, 3), axis=0)


def shell_at(P, m):
    """the model shell nearest the placed part's centroid"""
    c = P.mean(0) @ m[:3, :3].T + m[:3, 3]
    return min(range(len(SHELLS)), key=lambda k: np.linalg.norm(SHELLS[k].reshape(-1, 3).mean(0) - c))


def fit_yz(P, Q, about_origin, tx, it=80):
    """rotation about X (+ optional Y/Z shift) taking P onto surface samples Q"""
    tree = cKDTree(Q)
    a, t = 0.0, np.zeros(2)
    for _ in range(it):
        X = P[:, 1:] @ np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]]) + t
        _, j = tree.query(np.column_stack([P[:, 0] + tx, X]))
        Y = Q[j][:, 1:]
        A = P[:, 1:]
        if about_origin:
            ma, my = np.zeros(2), np.zeros(2)
        else:
            ma, my = A.mean(0), Y.mean(0)
        A0, Y0 = A - ma, Y - my
        a = np.arctan2((A0[:, 0] * Y0[:, 1] - A0[:, 1] * Y0[:, 0]).sum(), (A0 * Y0).sum())
        R2 = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        t = my - R2 @ ma
    return H(Rx(a), (tx, *t)), np.degrees(a)


def resid(P, m, k):
    d, _ = cKDTree(reg["sample"](SHELLS[k])).query(P @ m[:3, :3].T + m[:3, 3])
    return round(float(d.max()), 4), round(float(d.mean()), 4)


def main():
    out, rows = [], []

    def add(occ, part, kind, m, P, note="", k=None):
        k = shell_at(P, m) if k is None else k
        mx, mean = resid(P, m, k)
        out.append(dict(occurrence=occ, part=part, kind=kind, matrix=np.round(m, 7).tolist(), shell=k,
                        max_mm=mx, mean_mm=mean, note=note))
        print(f"{occ:26s} {kind:9s} shell {k:3d} max {mx:7.4f} mean {mean:.4f} {note}")

    for part in ("Main Base", "Servo Block", "Sub Base", "Eye Holder", "Three-Point Connector"):
        add(part, part, "identity", H(), verts(part))
    for part, stl in (("Eye Adaptor", "Eye Adaptor (x2)"), ("Fork", "Fork (x2)"),
                      ("PlaceHolder Eye", "PlaceHolder Eye (x2)")):
        P = verts(stl)
        add(part + " L", stl, "identity", H(), P)
        m = H(t=(75, 0, 0))
        add(part + " R", stl, "copy+75", m, P, "model mirrors this one",
            k=shell_at(P @ MX + [75, 0, 0], H()))
    lid = {}
    for side in ("Top", "Bottom"):
        P = verts(f"{side} Left Lid")
        k = shell_at(P, H())
        m, deg = fit_yz(P, reg["sample"](SHELLS[k]), True, 0.0)
        lid[side] = m
        add(f"{side} Left Lid", f"{side} Left Lid", "lid", m, P, f"{deg:+.3f} deg about X", k)
        PR = verts(f"{side} Right Lid")
        dz, _ = cKDTree(PR).query(P * [1, 1, -1])
        mr = refl_x(37.5) @ m @ H(np.diag([1, 1, -1.0]))
        assert np.linalg.det(mr[:3, :3]) > 0
        add(f"{side} Right Lid", f"{side} Right Lid", "rlid", mr, PR,
            f"Right STL = Left reflected in Z to {dz.max():.4f} mm")
    for part, stl in (("Top Lid Link", "Top Lid Link (x2)"), ("Bottom Lid Link", "Bottom Lid Link (x2)"),
                      ("Y-Arm", "Y-Arm")):
        P = verts(stl)
        xmid = (P[:, 0].min() + P[:, 0].max()) / 2
        # the shell: same volume, nearest after register.py's shift
        v = reg["mass"](load(os.path.join(KIT, stl + ".stl"))[0])[0]
        k = [i for i, s in enumerate(SHELLS) if abs(reg["mass"](s)[0] - v) < 3][0]   # one shell each in the model
        S = SHELLS[k].reshape(-1, 3)
        tx = (S[:, 0].min() + S[:, 0].max()) / 2 - xmid
        m, deg = fit_yz(P, reg["sample"](SHELLS[k]), False, tx)
        add(part + (" L" if "Link" in part else ""), stl, "plate", m, P,
            f"{deg:+.3f} deg about X, x shift {tx:+.4f}", k)
        if "Link" in part:
            mr = refl_x(37.5) @ m @ refl_x(xmid)
            assert np.linalg.det(mr[:3, :3]) > 0
            out.append(dict(occurrence=part + " R", part=stl, kind="mirror", matrix=np.round(mr, 7).tolist(),
                            shell=None, max_mm=None, mean_mm=None, note="not in Complete Model"))
            print(f"{part + ' R':26s} mirror    (not in Complete Model)")
    json.dump(out, open(sys.argv[3], "w"), indent=1)


main()
