#!/usr/bin/env python3
"""Generate carrier.kicad_pcb: outline from the DXF, the four rack holes with
pour keepouts, footprints linked to the schematic symbols, B.Cu routing and a
GND pour.  Everything is in BOARD coordinates (DXF x, -DXF y, mm) and shifted
by OX/OY onto the page at write time.

Routing (V2, Scott's placement, 2026-09-26) -- all B.Cu, no crossings:
  +12V  J1.1 (45.05,15.7) east under J1 to x=50.5, north to TP1; the y=2 run tees
        off it under the LM2596 to IN+.  J1 sits below the buck between H4 and the
        chamfer (Scott's placement), wire entry toward the PCA edge = the back of
        the box; the wires leave over the chamfered corner.  Earlier it stood on
        the right edge with the entry facing that edge - no way to get wires in -
        and my first move left its body against the buck's IN- corner.
  +5V   OUT+ -> lane x=20.5 (slot edge .. U3) -> y=11.2 over H4 -> lane x=33.8
        outside the PCA right row -> front-edge bar y=34.5 -> x=-37.9 up the
        left wing -> TP2 / y=10.9 under U1's outer row -> x=-53 (USB end) ->
        y=-2 through the module middle -> VCC pin 35.  U2.7 stubs down to the bar.
  +3V3  pin 16 -> module middle y=-12 -> USB end x=-52.5 -> y=-23.5 behind U1
        -> lane x=-17.2 beside the slot -> y=28.478 into PCA left-row VCC.
  I2C   pads 24/26 -> east along y=9.3/10.5 -> lanes x=-23.6/-24.8 east of H3
        -> PCA left row pads 3/4 from inside the module.
  GND   pour.  It reaches the left wing through the strip under the +5V bar
        (y 35.6..36.5) and the far-left strip (x -55.4..-54.1); the pocket
        west of the PCA left row drains under pad 1 (bar at 34.5 leaves 0.89).
  Rejected: I2C to the RIGHT row across the front bar (crosses the +3V3 lane);
  +3V3 down the far-left edge (fills the only GND path to U1's middle); any
  track under the antenna end (IO21/22 are inner-row pins, so they stay unused).
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
# Back chamfers: the DXF had a kink 13 mm in from each back corner (Scott's
# cleanup of the Fusion export moved a line).  Corner-to-corner still stuck out
# past the green case panel in the 2026-09-26 wood check, so the chamfer is the
# corner-to-corner line moved 4 mm inward, parallel (Scott's estimate, not a
# measurement of the panel): back-edge end -40.598 -> -35.420, side end
# 18.361 -> 12.061, mirrored about the board's x centre (0.016).
OUTLINE = [(35.452, 37.041), (-35.420, 37.041), (-55.950, 12.061),
           (-55.950, -11.852), (-58.931, -27.035), (-58.931, -35.125), (-58.772, -35.261),
           (-10.883, -35.261), (-10.883, -26.121), (-15.765, -21.771), (-15.765, 3.856),
           (0.016, 3.856), (15.797, 3.856), (15.797, -21.771), (10.915, -26.121),
           (10.915, -35.261), (58.803, -35.261), (58.963, -35.125), (58.963, -27.035),
           (55.982, -11.852), (55.982, 12.061)]
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
from footprints import D1_NAMES, D1_FLASH, PCA_NAMES  # noqa: E402
NETS = {
    "U1": {str(k): v for k, v in D1_NETS.items()},
    "U2": {str(k): v for k, v in {**PCA_NETS_L, **PCA_NETS_R}.items()},
    "U3": {"1": "+12V", "2": "GND", "3": "+5V", "4": "GND"},
    "J1": {"1": "+12V", "2": "GND"},
    "C1": {"1": "+5V", "2": "GND"}, "C2": {"1": "+5V", "2": "GND"},
    "R1": {"1": "+5V", "2": "RAIL_ADC"}, "R2": {"1": "RAIL_ADC", "2": "GND"},
}
# no-connect pins: the schematic netlist names each one unconnected-(REF-PIN-PadN)
# and DRC schematic parity wants the pad to carry that exact net (Scott saw 30
# "pad missing net" parity errors in the GUI before this was added)
for n in range(1, 41):
    if n not in D1_FLASH and n not in D1_NETS:
        NETS["U1"][str(n)] = f"unconnected-(U1-{D1_NAMES[n]}-Pad{n})"
for n in range(1, 13):
    if str(n) not in NETS["U2"]:
        NETS["U2"][str(n)] = f"unconnected-(U2-{PCA_NAMES[(n - 1) % 6]}-Pad{n})"
for r, (_, v, *_r) in PLACE.items():
    if r.startswith("TP"):
        NETS[r] = {"1": v}

POWER_W, SIG_W = 1.0, 0.6
# (net, width, polyline)
TRACKS = [
    # ---- +12V: jack terminal -> test point, and along y=2 under the LM2596 to IN+
    # J1.1 east under its own body, north to TP1's row, east onto TP1.  The
    # vertical sits at x=47.5, not 50.5: with the back chamfer 4 mm deeper the
    # pour's only path from the right edge round the bend into the J1 pocket
    # was pinched to 0.1 mm (poured as two islands); at 47.5 that path is 3.7 mm
    # and TP5 keeps pour on its west side.  Straight north from J1.1 would graze
    # IN- by 0.05.
    ("+12V", POWER_W, [(45.05, 15.7), (47.5, 15.7), (47.5, -5.0), (50.5, -5.0)]),
    ("+12V", POWER_W, [(47.5, 2.0), (25.7, 2.0), (25.7, 8.4)]),
    # ---- +5V trunk: OUT+ -> lane between the slot and U3 -> east above H4 ->
    #      lane outside the PCA right row -> front-edge bar -> up the left wing
    ("+5V", POWER_W, [(25.7, -31.4), (20.5, -26.2), (20.5, 11.2), (33.8, 11.2), (33.8, 34.5),
                      (-33.8, 34.5), (-33.8, 18.2), (-35.0, 17.0)]),              # ends on TP2; turns north at -33.8 (was -37.9: outside the 4 mm-deeper back chamfer)
    ("+5V", POWER_W, [(29.226, 34.5), (29.226, 31.018)]),                        # U2.7 from below
    # left wing: TP2 -> under U1's outer row -> USB end -> module middle -> VCC (35, inner row)
    ("+5V", POWER_W, [(-35.0, 17.0), (-37.9, 17.0), (-37.9, 10.9), (-53.0, 10.9), (-53.0, -2.0),
                      (-43.85, -2.0), (-43.85, 4.93)]),
    # C1.1 from the lane, not from the y=10.9 run: a stub down from 10.9 walled
    # off a pocket around C1.2 that hung on that pad's spoke alone
    ("+5V", POWER_W, [(-37.9, 17.0), (-39.75, 17.0)]),   # C1.1: Scott turned C1 180 and slid it to y=17 so the TP2 stub continues west (was a diagonal off the lane at y=25)
    ("+5V", POWER_W, [(-51.5, 10.9), (-51.5, 13.0)]),                            # C2.1
    # ---- +3V3: pin 16 (inner row) -> module middle -> USB end -> behind U1 ->
    #      lane beside the slot -> PCA left row VCC from inside the module
    ("+3V3", POWER_W, [(-43.85, -17.93), (-43.85, -12.0), (-52.5, -12.0), (-52.5, -23.5),
                       (-17.2, -23.5), (-17.2, 28.478), (-29.194, 28.478)]),
    ("+3V3", POWER_W, [(-40.0, -23.5), (-40.0, -27.0)]),                         # TP3
    # ---- I2C: both leave the outer row eastward, round H3 on its east side,
    #      into the PCA left row from inside.  Pad 24 (east) = outer lane = SDA.
    ("SDA", SIG_W, [(-28.61, 7.47), (-28.61, 9.3), (-23.6, 9.3), (-23.6, 25.938), (-29.194, 25.938)]),
    ("SCL", SIG_W, [(-31.15, 7.47), (-31.15, 10.5), (-24.8, 10.5), (-24.8, 23.398), (-29.194, 23.398)]),
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
    items.append(gr_text("EYES CARRIER V2 2026-09-26", -58.0, -33.2, 1.2))
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
