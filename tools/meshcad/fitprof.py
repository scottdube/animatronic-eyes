# Fit circles to ranges of a 2-column profile on stdin: args are "lo:hi" ranges of the first column.
import sys, numpy as np
sys.path.insert(0, sys.argv[1]); from stlmesh import circfit
P = np.loadtxt(sys.stdin)
for rg in sys.argv[2:]:
    lo, hi = map(float, rg.split(":")); zf = None
    if "@" in rg: pass
    Q = P[(P[:,0] >= lo) & (P[:,0] <= hi)]
    cx, cy, R, res, n = circfit(Q)
    print(f"[{lo},{hi}] n{n} centre ({cx:+.4f},{cy:+.4f}) R {R:.4f} maxres {res:.4f}")
