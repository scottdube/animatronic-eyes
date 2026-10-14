# Mirror a spec's FEATURES across a drawing-frame plane (coordinate k -> -k), for kit parts that are exact mirror
# images of another (the Right lids are the Left lids with STL z negated: mircmp max 0.0000 mm). Arcs reverse
# their turning sense; a feature extruded along k swaps and negates lo/hi; a rotate op about any axis but k turns
# the other way (S R(a) S = R(-a)).
import importlib.util, os

_UV = {"x": (1, 2), "y": (0, 2), "z": (0, 1)}
_I = {"x": 0, "y": 1, "z": 2}


def load(name):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".py")
    sp = importlib.util.spec_from_file_location("spec_" + name, path)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _pt(p, s):
    return (p[0] * s[0], p[1] * s[1])


def _loop(lp, s, flip):
    start, segs = lp
    return (_pt(start, s), [("L", _pt(g[1], s)) if g[0] == "L" else ("A", _pt(g[1], s), _pt(g[2], s), g[3] * flip)
                            for g in segs])


def mirror(features, k):
    out = []
    for f in features:
        f = dict(f)
        assert f["op"] != "chamfer", "mirror: chamfer picks not handled"
        k_i = _I[k]
        if f["op"] == "rotate":
            if f["axis"] != k:
                f["deg"] = -f["deg"]
            out.append(f)
            continue
        if f["axis"] == k:
            s, flip = (1, 1), 1
            f["lo"], f["hi"] = -f["hi"], -f["lo"]
        else:
            s = (-1, 1) if _UV[f["axis"]][0] == k_i else (1, -1)
            flip = -1
        if "circle" in f:
            f["circle"] = (_pt(f["circle"][0], s), f["circle"][1])
        if "loop" in f:
            f["loop"] = _loop(f["loop"], s, flip)
        if "runs" in f:
            f["runs"] = [[_pt(p, s) for p in run] for run in f["runs"]]
        if "revolve" in f:
            r = dict(f["revolve"])
            r["centre"] = _pt(r["centre"], s)
            if f["axis"] == k:                                  # w -> -w in the (r, w) half-section
                r["loop"] = _loop(r["loop"], (1, -1), -1)
            f["revolve"] = r
        out.append(f)
    return out
