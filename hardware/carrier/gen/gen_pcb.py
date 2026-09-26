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

# ref -> (footprint, value, x, y, rot)
PLACE = {
    "U2": ("PCA9685_Adafruit_Module", "PCA9685 16ch servo", 0, -22.56, 0),
    "U1": ("D1_Mini_ESP32_THT", "D1 Mini ESP32 (Type-C)", 0, 18.0, 0),
    "U3": ("LM2596_Module", "LM2596 buck 12V->5.05V", 51.6, 17.9, 180),
    "J1": ("KF301_1x02_P5.08", "12V pigtail", 36.5, 31.0, 180),
    "C1": ("CP_Radial_D6.3_P2.5", "220u", 22.25, 33.3, 0),
    "C2": ("C_Disc_P5.08", "100n", 22.5, 0.0, 90),
    "R1": ("R_Axial_P10.16", "10k", -36.0, -8.0, 270),
    "R2": ("R_Axial_P10.16", "10k", -39.5, 2.16, 90),
    "TP1": ("TestPoint_THT_D2.2_1.181", "+12V", 40.0, 24.0, 0),
    "TP2": ("TestPoint_THT_D2.2_1.181", "+5V", 24.0, -8.0, 0),
    "TP3": ("TestPoint_THT_D2.2_1.181", "+3V3", -44.0, -18.88, 0),
    "TP4": ("TestPoint_THT_D2.2_1.181", "RAIL_ADC", -43.0, 2.16, 0),
    "TP5": ("TestPoint_THT_D2.2_1.181", "GND", 26.0, 4.0, 0),
    "TP6": ("TestPoint_THT_D2.2_1.181", "GND", -43.0, -8.0, 0),
}
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
    ("+12V", POWER_W, [(36.5, 31.0), (36.5, 20.4), (34.0, 17.9)]),
    ("+12V", POWER_W, [(36.5, 24.0), (40.0, 24.0)]),
    ("+5V", POWER_W, [(34.0, -21.9), (34.0, -16.34), (29.21, -16.34)]),
    ("+5V", POWER_W, [(29.21, -16.34), (29.21, -8.0), (19.2, -8.0), (19.2, 33.3), (22.25, 33.3)]),
    ("+5V", POWER_W, [(19.2, 31.4), (8.0, 31.4), (8.0, 24.35), (11.43, 24.35)]),
    ("+5V", POWER_W, [(19.2, 0.0), (22.5, 0.0)]),
    ("+5V", POWER_W, [(-29.21, -16.34), (-36.0, -16.34), (-36.0, -8.0)]),
    ("+3V3", POWER_W, [(-11.43, 24.35), (-9.5, 24.35), (-9.5, 31.4), (-17.2, 31.4),
                       (-17.2, -18.88), (-44.0, -18.88)]),
    ("RAIL_ADC", SIG_W, [(-11.43, 9.11), (-8.0, 9.11), (-8.0, 33.0), (-18.9, 33.0),
                         (-18.9, 2.16), (-43.0, 2.16)]),
    ("SDA", SIG_W, [(29.21, -21.42), (17.85, -21.42), (17.85, 11.65), (13.97, 11.65)]),
    ("SCL", SIG_W, [(29.21, -23.96), (16.7, -23.96), (16.7, 9.11), (13.97, 9.11)]),
]

# pour keepouts (name, polygon)
def circle(cx, cy, r, n=24):
    import math
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rectp(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


KEEPOUTS = [(f"H{i} standoff", circle(hx, hy, HOLE_KEEPOUT_R)) for i, (hx, hy) in enumerate(HOLES, 1)]
KEEPOUTS += [("D1 antenna", rectp(-15.7, -1.5, 15.7, 5.4)),
             ("D1 flash pins L", rectp(-15.2, 25.6, -10.2, 30.7)),
             ("D1 flash pins R", rectp(10.2, 25.6, 15.2, 30.7))]

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
        if rot:
            blk = re.sub(r'\(at ([-\d.]+) ([-\d.]+)\)', rf'(at \1 \2 {rot})', blk, 1)
        if num in nets:
            blk = blk.replace('(remove_unused_layers no)', f'(remove_unused_layers no)\n\t\t(net "{nets[num]}")', 1)
        return blk
    t = re.sub(r'\(pad "([^"]*)" thru_hole[\s\S]*?\n\t\)', fix_pad, t)
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
    for name, poly in KEEPOUTS:
        items.append(keepout(name, poly))
    items.append(gnd_pour(rectp(-60, -36, 60, 38)))
    # legend
    items.append(gr_text("EYES CARRIER V1 2026-09-25", -40.0, 36.0, 0.9))
    items.append(gr_text("SERVO RAIL ADC", -47.0, 5.5, 0.8))
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
    for r in ("U1", "U2", "U3", "R1", "R2", "C2", "J1"):
        print(r, {n: p for n, p in pads[r].items() if n in NETS.get(r, {})})
    bad = check_tracks(pads)
    print("dangling track ends:", bad or "none")
    print("wrote", os.path.join(outdir, "carrier.kicad_pcb"))
