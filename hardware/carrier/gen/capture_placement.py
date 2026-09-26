#!/usr/bin/env python3
"""Copy footprint positions from carrier.kicad_pcb (Scott's GUI placement) into
placement.py.  Run with KiCad CLOSED, then `python3 gen/gen_pcb.py` to rebuild.
Holes H1-H4 are skipped: they come from the DXF via gen_pcb.HOLES."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
pcb = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "carrier.kicad_pcb")
OX = OY = 100.0
s = open(pcb).read()
place = {}
i = 0
while True:
    j = s.find("\n\t(footprint ", i)
    if j < 0:
        break
    d, k = 0, j + 1
    while True:
        if s[k] == "(":
            d += 1
        elif s[k] == ")":
            d -= 1
            if d == 0:
                break
        k += 1
    fp = s[j:k + 1]; i = k
    name = re.match(r'\n\t\(footprint "carrier:([^"]+)"', fp).group(1)
    ref = re.search(r'\(property "Reference" "([^"]+)"', fp).group(1)
    val = re.search(r'\(property "Value" "([^"]*)"', fp).group(1)
    m = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', fp)
    if ref.startswith("H"):
        continue
    place[ref] = (name, val, round(float(m.group(1)) - OX, 3), round(float(m.group(2)) - OY, 3), float(m.group(3) or 0))
order = ["U1", "U2", "U3", "J1", "C1", "C2"] + sorted(r for r in place if r.startswith("TP"))
out = open(os.path.join(HERE, "placement.py")).read()
body = "PLACE = {\n" + "".join(f'    "{r}": {place[r]!r},\n' for r in order if r in place) + "}\n"
out = out[:out.index("PLACE = {")] + body
open(os.path.join(HERE, "placement.py"), "w").write(out)
print("captured", len(place), "footprints ->", os.path.join(HERE, "placement.py"))
