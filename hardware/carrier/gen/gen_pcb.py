#!/usr/bin/env python3
"""Generate carrier.kicad_pcb: outline from the DXF, the four rack holes with
pour keepouts, footprints linked to the schematic symbols, B.Cu routing and a
GND pour.  Everything is in BOARD coordinates (DXF x, -DXF y, mm) and shifted
by OX/OY onto the page at write time.

Routing topology (why the pins are what they are is in gen_sch.py):
  right strip (between the notch edge x=15.8 and the lower-right hole keepout
  x=25.2) carries three lanes: SCL 16.7, SDA 17.85, +5V 19.2.
  left strip carries +3V3 17.2 and RAIL_ADC 18.9.
  corridor below the D1 Mini's last pin row (y 30.9..36.5) carries +5V on the
  right half, +3V3 and RAIL_ADC on the left half; nothing crosses.
"""
import os
import re
import sys
import uuid as uuidlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexp
import footprints as F

NS = uuidlib.UUID("a11e5c0d-0000-4000-8000-0000000000b0")
_n = [0]


def uid():
    _n[0] += 1
    return str(uuidlib.uuid5(NS, str(_n[0])))


OX, OY = 100.0, 100.0


def P(x, y):
    return f"{round(x + OX, 3):g} {round(y + OY, 3):g}"


# ------------------------------------------------------------- geometry
# outline.dxf polyline, DXF y flipped (KiCad y grows downward)
OUTLINE = [(40.630, 37.041), (-40.598, 37.041), (-47.326, 24.189), (-55.950, 18.361),
           (-55.950, -11.852), (-58.931, -27.035), (-58.931, -35.125), (-58.772, -35.261),
           (-10.883, -35.261), (-10.883, -26.121), (-15.765, -21.771), (-15.765, 3.856),
           (0.016, 3.856), (15.797, 3.856), (15.797, -21.771), (10.915, -26.121),
           (10.915, -35.261), (58.803, -35.261), (58.963, -35.125), (58.963, -27.035),
           (55.982, -11.852), (55.982, 18.361), (47.358, 24.189)]
HOLES = [(-49.481, -27.738), (49.513, -27.738), (-28.455, 15.270), (28.487, 15.270)]
HOLE_KEEPOUT_R = 3.25        # M3 nylon standoff hex + washer

# ref -> (footprint, value, x, y, rot): Scott places in the KiCad GUI, then
# `python3 gen/capture_placement.py` copies the positions into placement.py and
# this script rebuilds the board around them (outline, keepouts, pour, fresh
# footprint copies).  Never edit placement.py by hand while KiCad is open.
from placement import PLACE   # noqa: E402
for i, (hx, hy) in enumerate(HOLES, 1):
    PLACE[f"H{i}"] = ("MountingHole_M3_3.175", "M3 rack standoff", hx, hy, 0)

# pad nets, ref -> {pad: net}
from gen_sch import D1_NETS, PCA_NETS_L, PCA_NETS_R   # noqa: E402  (same source of truth)
NETS = {
    "U1": {str(k): v for k, v in D1_NETS.items()},
    "U2": {str(k): v for k, v in {**PCA_NETS_L, **PCA_NETS_R}.items()},
    "U3": {"1": "+12V", "2": "GND", "3": "+5V", "4": "GND"},
    "J1": {"1": "+12V", "2": "GND"},
    "C1": {"1": "+5V", "2": "GND"}, "C2": {"1": "+5V", "2": "GND"},
    "R1": {"1": "+5V", "2": "RAIL_ADC"}, "R2": {"1": "RAIL_ADC", "2": "GND"},
}
for r, (_, v, *_r) in PLACE.items():
    if r.startswith("TP"):
        NETS[r] = {"1": v}

POWER_W, SIG_W = 1.0, 0.6
# (net, width, polyline)
TRACKS = [
    # empty: V1's routing (commit 6c48d78) belonged to the rejected placement.
    # Route here once Scott's placement is frozen, or in the GUI (then the
    # generator stops being the master for copper).
]

# pour keepouts (name, polygon)
def circle(cx, cy, r, n=24):
    import math
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rectp(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


KEEPOUTS = [(f"H{i} standoff", circle(hx, hy, HOLE_KEEPOUT_R)) for i, (hx, hy) in enumerate(HOLES, 1)]


def d1_keepouts():
    """Antenna end and the two flash-pin blocks, in U1's local frame, moved with it."""
    fp, val, ux, uy, ur = PLACE["U1"]
    # antenna keepout runs to the pin-1 row centre line: stopping short of the pads
    # leaves a copper sliver that becomes an island on a thermal spoke
    local = [("D1 antenna", rectp(-15.7, -19.5, 15.7, -11.43)),
             ("D1 flash pins L", rectp(-15.2, 7.6, -10.2, 12.7)),
             ("D1 flash pins R", rectp(10.2, 7.6, 15.2, 12.7))]
    out = []
    for name, poly in local:
        out.append((name, [(ux + rot_xy(x, y, ur)[0], uy + rot_xy(x, y, ur)[1]) for x, y in poly]))
    return out

# ------------------------------------------------------------- helpers
def rot_xy(x, y, rot):
    import math
    t = math.radians(rot)
    return (x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t))


def symbol_uuids(sch_path):
    tree = sexp.parse(open(sch_path).read())
    out = {}
    for s in sexp.find(tree, "symbol"):
        if not sexp.find(s, "lib_id"):
            continue
        u = sexp.first(s, "uuid")
        ref = None
        for p in sexp.find(s, "property"):
            if p[1] == '"Reference"':
                ref = p[2].strip('"')
        if ref and u:
            out[ref] = u[1].strip('"')
    return out


PAD_RE = re.compile(r'\(pad "([^"]*)" (thru_hole|np_thru_hole) \w+\n\t\t\(at ([-\d.]+) ([-\d.]+)\)')


def pad_positions(fp_text, x, y, rot):
    out = {}
    for m in PAD_RE.finditer(fp_text):
        if m.group(1):
            dx, dy = rot_xy(float(m.group(3)), float(m.group(4)), rot)
            out[m.group(1)] = (round(x + dx, 3), round(y + dy, 3))
    return out


def embed(ref, fpname, value, x, y, rot, sym_uuid, nets):
    F._n[0] = 0
    t = F.ALL[fpname]()
    head_old = t[:t.index('\t(descr')]
    t = (f'(footprint "carrier:{fpname}"\n\t(layer "F.Cu")\n\t(uuid "{uid()}")\n'
         f'\t(at {P(x, y)} {rot})\n') + t[len(head_old):]
    t = t.replace('(property "Reference" "REF**"', f'(property "Reference" "{ref}"', 1)
    t = t.replace(f'(property "Value" "{fpname}"', f'(property "Value" "{value}"', 1)
    t = t.replace('\t(attr through_hole)',
                  f'\t(path "/{sym_uuid}")\n\t(sheetname "/")\n\t(sheetfile "carrier.kicad_sch")\n\t(attr through_hole)', 1)
    # pad nets + footprint rotation folded into the pad angle
    def fix_pad(m):
        num = m.group(1)
        blk = m.group(0)
        if num in nets:
            blk = blk.replace('(remove_unused_layers no)', f'(remove_unused_layers no)\n\t\t(net "{nets[num]}")', 1)
        return blk
    t = re.sub(r'\(pad "([^"]*)" (?:np_)?thru_hole[\s\S]*?\n\t\)', fix_pad, t)
    # KiCad stores pad AND text angles absolute (footprint angle included); a
    # pad or text left at 0 in a rotated footprint reads as rotated the other
    # way, which is what "does not match copy in library" was reporting
    if rot:
        body_start = t.index('\n\t(property ')
        t = t[:body_start] + re.sub(r'\(at ([-\d.]+) ([-\d.]+)(?: 0)?\)', rf'(at \1 \2 {rot})', t[body_start:])
    # every uuid inside must be unique on the board
    t = re.sub(r'\(uuid "[^"]+"\)', lambda m: f'(uuid "{uid()}")', t)
    return "\n".join("\t" + ln for ln in t.rstrip("\n").split("\n"))


def segment(net, w, a, b):
    return (f'\t(segment\n\t\t(start {P(*a)})\n\t\t(end {P(*b)})\n\t\t(width {w})\n'
            f'\t\t(layer "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid()}")\n\t)')


def gr_line(a, b, layer="Edge.Cuts", w=0.1):
    return (f'\t(gr_line\n\t\t(start {P(*a)})\n\t\t(end {P(*b)})\n\t\t(stroke\n\t\t\t(width {w})\n'
            f'\t\t\t(type default)\n\t\t)\n\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n\t)')


def gr_text(s, x, y, size=1.0, layer="F.SilkS", justify="left bottom"):
    return (f'\t(gr_text "{s}"\n\t\t(at {P(x, y)} 0)\n\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n'
            f'\t\t\t(justify {justify})\n\t\t)\n\t)')


def pts(poly):
    return " ".join(f"(xy {P(*p)})" for p in poly)


def keepout(name, poly):
    return (f'\t(zone\n\t\t(layer "B.Cu")\n\t\t(uuid "{uid()}")\n\t\t(name "{name}")\n\t\t(hatch edge 0.5)\n'
            f'\t\t(connect_pads\n\t\t\t(clearance 0)\n\t\t)\n\t\t(min_thickness 0.25)\n'
            f'\t\t(keepout\n\t\t\t(tracks allowed)\n\t\t\t(vias allowed)\n\t\t\t(pads allowed)\n'
            f'\t\t\t(copperpour not_allowed)\n\t\t\t(footprints allowed)\n\t\t)\n'
            f'\t\t(placement\n\t\t\t(enabled no)\n\t\t\t(sheetname "/")\n\t\t)\n'
            f'\t\t(fill\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(island_removal_mode 0)\n\t\t)\n'
            f'\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{pts(poly)}\n\t\t\t)\n\t\t)\n\t)')


def gnd_pour(poly):
    return (f'\t(zone\n\t\t(net "GND")\n\t\t(locked yes)\n\t\t(layer "B.Cu")\n\t\t(uuid "{uid()}")\n'
            f'\t\t(name "GND pour")\n\t\t(hatch edge 0.5)\n\t\t(priority 0)\n'
            f'\t\t(connect_pads thru_hole_only\n\t\t\t(clearance 0.6)\n\t\t)\n\t\t(min_thickness 0.5)\n'
            f'\t\t(fill yes\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(island_removal_mode 0)\n\t\t)\n'
            f'\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{pts(poly)}\n\t\t\t)\n\t\t)\n\t)')


# ------------------------------------------------------------- build
def build(outdir):
    uuids = symbol_uuids(os.path.join(outdir, "carrier.kicad_sch"))
    items = []
    pads = {}
    for ref, (fp, val, x, y, rot) in PLACE.items():
        items.append(embed(ref, fp, val, x, y, rot, uuids[ref], NETS.get(ref, {})))
        pads[ref] = pad_positions(F.ALL[fp](), x, y, rot)
    # outline
    for i, a in enumerate(OUTLINE):
        items.append(gr_line(a, OUTLINE[(i + 1) % len(OUTLINE)]))
    # routing
    for net, w, poly in TRACKS:
        for a, b in zip(poly, poly[1:]):
            items.append(segment(net, w, a, b))
    # zones: keepouts first, pour last
    for name, poly in KEEPOUTS + d1_keepouts():
        items.append(keepout(name, poly))
    items.append(gnd_pour(rectp(-60, -36, 60, 38)))
    # legend
    items.append(gr_text("EYES CARRIER V2 2026-09-25", -58.0, -33.2, 0.9))
    doc = open(os.path.join(HERE, "pcb_header.sexp")).read().rstrip("\n")
    doc += "\n" + "\n".join(items) + "\n\t(embedded_fonts no)\n)\n"
    open(os.path.join(outdir, "carrier.kicad_pcb"), "w").write(doc)
    return pads


def check_tracks(pads):
    """Every polyline end must sit on a pad of its own net (or on another
    segment of the same net); report anything that does not."""
    bad = []
    for net, w, poly in TRACKS:
        for end in (poly[0], poly[-1]):
            hit = any(abs(px - end[0]) < 0.01 and abs(py - end[1]) < 0.01 and NETS.get(r, {}).get(n) == net
                      for r, pp in pads.items() for n, (px, py) in pp.items())
            if not hit:
                # on another segment of the same net?
                on_seg = False
                for net2, w2, poly2 in TRACKS:
                    if net2 != net or poly2 is poly:
                        continue
                    for a, b in zip(poly2, poly2[1:]):
                        if min(a[0], b[0]) - 1e-6 <= end[0] <= max(a[0], b[0]) + 1e-6 and \
                           min(a[1], b[1]) - 1e-6 <= end[1] <= max(a[1], b[1]) + 1e-6 and \
                           abs((b[0] - a[0]) * (end[1] - a[1]) - (b[1] - a[1]) * (end[0] - a[0])) < 1e-6:
                            on_seg = True
                if not on_seg:
                    bad.append((net, end))
    return bad


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    pads = build(outdir)
    for r in ("U1", "U2", "U3", "C2", "J1"):
        print(r, {n: p for n, p in pads[r].items() if n in NETS.get(r, {})})
    bad = check_tracks(pads)
    print("dangling track ends:", bad or "none")
    print("wrote", os.path.join(outdir, "carrier.kicad_pcb"))
