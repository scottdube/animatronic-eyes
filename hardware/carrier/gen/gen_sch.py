#!/usr/bin/env python3
"""Generate carrier.kicad_sch (KiCad 10) for the eyes carrier board.

Stock symbols are embedded from the installed KiCad libraries; the three
modules are drawn here as 'carrier:*' symbols whose pin NUMBERS are header
positions and pin NAMES are the silk labels.  Nets are made with global
labels so the PCB net names have no sheet prefix and the Power netclass
patterns (GND, +5V, +3V3, +12V) match them.
"""
import os
import sys
import uuid as uuidlib

sys.path.insert(0, os.path.dirname(__file__))
import sexp
from footprints import D1_NAMES, D1_FLASH, PCA_NAMES

LIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
NS = uuidlib.UUID("a11e5c0d-0000-4000-8000-0000000000e5")
SHEET = "a11e5c0d-0000-4000-8000-00000000c0de"
PROJECT = "carrier"
_n = [0]


def uid():
    _n[0] += 1
    return str(uuidlib.uuid5(NS, str(_n[0])))


FONT = "(effects\n\t\t\t\t\t(font\n\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t)\n\t\t\t\t)"

# ---------------------------------------------------------------- symbols
_cache, used, custom = {}, {}, {}


def libsym(lib, name):
    if (lib, name) not in _cache:
        tree = sexp.parse(open(f"{LIB}/{lib}.kicad_sym").read())
        for s in sexp.find(tree, "symbol"):
            if s[1] == f'"{name}"':
                _cache[(lib, name)] = s
                break
        else:
            raise KeyError(f"{lib}:{name}")
    return _cache[(lib, name)]


def pins_of(lib, name):
    if lib == "carrier":
        return custom[name][1]
    out = {}
    for sub in sexp.find(libsym(lib, name), "symbol"):
        for p in sexp.find(sub, "pin"):
            at = sexp.first(p, "at")
            out[sexp.first(p, "number")[1].strip('"')] = (float(at[1]), float(at[2]))
    return out


def define_module(name, left, right, width, descr, ref="U"):
    """A box symbol. left/right: lists of (number, pin_name) top to bottom,
    pitch 2.54. Returns nothing; registers the lib text and pin map."""
    rows = max(len(left), len(right))
    h = (rows + 1) * 2.54
    top = round(h / 2, 2)
    hw = width / 2
    pins, body = {}, []
    for side, lst in (("L", left), ("R", right)):
        for i, (num, pname) in enumerate(lst):
            y = round(top - 2.54 * (i + 1), 2)
            if side == "L":
                x, rot = -hw - 2.54, 0
            else:
                x, rot = hw + 2.54, 180
            pins[str(num)] = (x, y)
            body.append(
                f"\t\t\t(pin passive line\n\t\t\t\t(at {x} {y} {rot})\n\t\t\t\t(length 2.54)\n"
                f'\t\t\t\t(name "{pname}"\n\t\t\t\t\t{FONT}\n\t\t\t\t)\n'
                f'\t\t\t\t(number "{num}"\n\t\t\t\t\t{FONT}\n\t\t\t\t)\n\t\t\t)')
    rect = (f"\t\t\t(rectangle\n\t\t\t\t(start {-hw} {top})\n\t\t\t\t(end {hw} {-top})\n"
            f"\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n"
            f"\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)\n\t\t\t)")
    text = (f'\t(symbol "carrier:{name}"\n\t\t(pin_names\n\t\t\t(offset 1.016)\n\t\t)\n'
            f"\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n"
            f"\t\t(duplicate_pin_numbers_are_jumpers no)\n"
            f'\t\t(property "Reference" "{ref}"\n\t\t\t(at 0 {top + 1.27} 0)\n\t\t\t{FONT}\n\t\t)\n'
            f'\t\t(property "Value" "{name}"\n\t\t\t(at 0 {-top - 1.27} 0)\n\t\t\t{FONT}\n\t\t)\n'
            f'\t\t(property "Footprint" ""\n\t\t\t(at 0 0 0)\n\t\t\t(hide yes)\n\t\t\t{FONT}\n\t\t)\n'
            f'\t\t(property "Datasheet" ""\n\t\t\t(at 0 0 0)\n\t\t\t(hide yes)\n\t\t\t{FONT}\n\t\t)\n'
            f'\t\t(property "Description" "{descr}"\n\t\t\t(at 0 0 0)\n\t\t\t(hide yes)\n\t\t\t{FONT}\n\t\t)\n'
            f'\t\t(symbol "{name}_0_1"\n{rect}\n\t\t)\n'
            f'\t\t(symbol "{name}_1_1"\n' + "\n".join(body) + "\n\t\t)\n"
            f"\t\t(embedded_fonts no)\n\t)")
    custom[name] = (text, pins)


def place_pin(px, py, x, y, rot, mirror):
    if mirror == "y":
        px = -px
    if rot == 0:
        dx, dy = px, -py
    elif rot == 90:
        dx, dy = py, px
    elif rot == 180:
        dx, dy = -px, py
    elif rot == 270:
        dx, dy = -py, -px
    else:
        raise ValueError(rot)
    return (round(x + dx, 4), round(y + dy, 4))


items = []
PROPS = lambda: "(show_name no)\n\t\t\t(do_not_autoplace no)"


def comp(lib, name, ref, value, x, y, rot=0, mirror=None, footprint="",
         ref_off=(0, -6.35), val_off=(0, 6.35)):
    used[(lib, name)] = True
    pins = pins_of(lib, name)
    body = [f'\t(symbol\n\t\t(lib_id "{lib}:{name}")\n\t\t(at {x} {y} {rot})']
    if mirror:
        body.append(f"\t\t(mirror {mirror})")
    body.append("\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n"
                f"\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(uuid \"{uid()}\")")
    for pname, pval, off, hide in (("Reference", ref, ref_off, False),
                                   ("Value", value, val_off, False),
                                   ("Footprint", footprint, (0, 0), True),
                                   ("Datasheet", "~", (0, 0), True),
                                   ("Description", "", (0, 0), True)):
        h = "\n\t\t\t(hide yes)" if hide else ""
        body.append(f'\t\t(property "{pname}" "{pval}"\n\t\t\t(at {round(x + off[0], 4)} {round(y + off[1], 4)} 0){h}\n'
                    f"\t\t\t{PROPS()}\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)")
    for num in sorted(pins, key=lambda s: (len(s), s)):
        body.append(f'\t\t(pin "{num}"\n\t\t\t(uuid "{uid()}")\n\t\t)')
    body.append(f'\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "/{SHEET}"\n'
                f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
    items.append("\n".join(body))
    return {n: place_pin(*p, x, y, rot, mirror) for n, p in pins.items()}


def wire(a, b):
    items.append(f"\t(wire\n\t\t(pts\n\t\t\t(xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})\n\t\t)\n"
                 f"\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid \"{uid()}\")\n\t)")


def glabel(text, at, rot=0):
    """Global label whose anchor is `at`; rot 0 reads to the right of the point,
    180 to the left."""
    just = "left" if rot == 0 else "right"
    items.append(f'\t(global_label "{text}"\n\t\t(shape input)\n\t\t(at {at[0]} {at[1]} {rot})\n'
                 f"\t\t(fields_autoplaced yes)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n"
                 f'\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{uid()}")\n'
                 f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {at[0]} {at[1]} 0)\n'
                 f"\t\t\t(hide yes)\n\t\t\t{PROPS()}\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n"
                 f"\t\t\t\t)\n\t\t\t\t(justify {just})\n\t\t\t)\n\t\t)\n\t)")


def noconn(at):
    items.append(f'\t(no_connect\n\t\t(at {at[0]} {at[1]})\n\t\t(uuid "{uid()}")\n\t)')


def note(text, at, size=1.27):
    esc = text.replace("\n", "\\n").replace('"', "'")
    items.append(f'\t(text "{esc}"\n\t\t(exclude_from_sim no)\n\t\t(at {at[0]} {at[1]} 0)\n'
                 f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n\t\t\t(justify left top)\n"
                 f'\t\t)\n\t\t(uuid "{uid()}")\n\t)')


def stub(p, net, side):
    """Wire a pin out 5.08 mm to a global label. side 'L' = pin faces left."""
    if side == "L":
        end = (round(p[0] - 5.08, 4), p[1])
        wire(p, end)
        glabel(net, end, 180)
    else:
        end = (round(p[0] + 5.08, 4), p[1])
        wire(p, end)
        glabel(net, end, 0)


# ---------------------------------------------------------------- circuit

# Single-sided routing decided these.  The D1 Mini's inner header columns
# can only leave the module through its middle and out below the last pin
# row; the outer columns can only leave sideways, into the strips beside the
# module, where any vertical lane blocks every pad facing it.  So:
#   * I2C on outer-right pads 24/26 (IO27 = SCL, IO25 = SDA) -> right strip
#     lanes to the PCA's right row.  Wire.begin(25, 27).
#   * rail divider on inner-left pad 4 (IO36, ADC1_CH0, input-only) -> exits
#     through the middle, corridor, left strip.  Rail.cpp PIN = 36.
#   * 3V3 (16) and VCC (35) are inner pins: middle -> corridor -> left/right.
#   * +5V reaches the divider from the PCA's LEFT V+ pin: the PCA rows are
#     paralleled on the module, declared as jumper pad groups on the footprint.
D1_NETS = {4: "RAIL_ADC", 16: "+3V3", 24: "SCL", 26: "SDA", 35: "+5V",
           1: "GND", 22: "GND", 33: "GND"}
PCA_NETS_L = {1: "+5V", 2: "+3V3", 6: "GND"}              # left row: power
PCA_NETS_R = {7: "+5V", 9: "SDA", 10: "SCL", 12: "GND"}   # right row (7-12)


def build():
    # --- symbols for the three modules
    left = [(n, D1_NAMES[n]) for n in range(1, 21) if n not in D1_FLASH]
    right = [(n, D1_NAMES[n]) for n in range(21, 41) if n not in D1_FLASH]
    define_module("D1_Mini_ESP32", left, right, 25.4,
                  "D1 Mini ESP32 module; pin numbers are header positions (r0oland ESP32_mini numbering); flash-bus positions 17 19 20 37 38 39 40 are NPTH and have no pin")
    define_module("PCA9685_Module", [(i + 1, PCA_NAMES[i]) for i in range(6)],
                  [(i + 7, PCA_NAMES[i]) for i in range(6)], 20.32,
                  "Adafruit-layout PCA9685 16ch servo driver on two 1x06 headers; rows are internally connected")
    define_module("LM2596_Module", [(1, "IN+"), (2, "IN-")], [(3, "OUT+"), (4, "OUT-")], 17.78,
                  "LM2596 adjustable buck module, set to 5.0-5.1 V BEFORE connecting")

    # --- U1 D1 Mini, centre of sheet
    u1 = comp("carrier", "D1_Mini_ESP32", "U1", "D1 Mini ESP32 (Type-C)", 203.2, 121.92,
              footprint="carrier:D1_Mini_ESP32_THT", ref_off=(0, -46), val_off=(0, 46))
    for n in range(1, 41):
        if n in D1_FLASH:
            continue
        p = u1[str(n)]
        side = "L" if n <= 20 else "R"
        if n in D1_NETS:
            stub(p, D1_NETS[n], side)
        else:
            noconn(p)

    # --- U2 PCA9685, right
    u2 = comp("carrier", "PCA9685_Module", "U2", "PCA9685 16ch servo", 304.8, 81.28,
              footprint="carrier:PCA9685_Adafruit_Module", ref_off=(0, -12.7), val_off=(0, 12.7))
    for n in range(1, 13):
        p = u2[str(n)]
        side = "L" if n <= 6 else "R"
        nets = PCA_NETS_L if n <= 6 else PCA_NETS_R
        if n in nets:
            stub(p, nets[n], side)
        else:
            noconn(p)

    # --- U3 LM2596 + J1 terminal, left
    u3 = comp("carrier", "LM2596_Module", "U3", "LM2596 buck 12V->5.05V", 101.6, 81.28,
              footprint="carrier:LM2596_Module", ref_off=(0, -7.62), val_off=(0, 7.62))
    stub(u3["1"], "+12V", "L")
    stub(u3["2"], "GND", "L")
    stub(u3["3"], "+5V", "R")
    stub(u3["4"], "GND", "R")
    j1 = comp("Connector", "Screw_Terminal_01x02", "J1", "12V pigtail", 50.8, 81.28,
              mirror="y", footprint="carrier:KF301_1x02_P5.08", ref_off=(0, -5.08), val_off=(0, 5.08))
    stub(j1["1"], "+12V", "R")
    stub(j1["2"], "GND", "R")

    # --- bulk + ceramic at the D1 Mini VCC pin
    for ref, sym, val, fp, x in (("C1", "C_Polarized", "220u", "carrier:CP_Radial_D6.3_P2.5", 101.6),
                                 ("C2", "C", "100n", "carrier:C_Disc_P5.08", 121.92)):
        c = comp("Device", sym, ref, val, x, 139.7, footprint=fp, ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
        wire(c["1"], (x, c["1"][1] - 2.54)); glabel("+5V", (x, c["1"][1] - 2.54), 0)
        wire(c["2"], (x, c["2"][1] + 2.54)); glabel("GND", (x, c["2"][1] + 2.54), 0)

    # --- rail divider: +5V - R1 - RAIL_ADC - R2 - GND  (10k/10k, GPIO36 = ADC1_CH0)
    r1 = comp("Device", "R", "R1", "10k", 60.96, 129.54, footprint="carrier:R_Axial_P10.16",
              ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
    r2 = comp("Device", "R", "R2", "10k", 60.96, 149.86, footprint="carrier:R_Axial_P10.16",
              ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
    wire(r1["1"], (60.96, r1["1"][1] - 2.54)); glabel("+5V", (60.96, r1["1"][1] - 2.54), 0)
    wire(r1["2"], r2["1"])
    mid = (60.96, 139.7)
    items.append(f'\t(junction\n\t\t(at 60.96 139.7)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{uid()}")\n\t)')
    wire(mid, (68.58, 139.7)); glabel("RAIL_ADC", (68.58, 139.7), 0)
    wire(r2["2"], (60.96, r2["2"][1] + 2.54)); glabel("GND", (60.96, r2["2"][1] + 2.54), 0)

    # --- test points
    # no SDA/SCL test points: the only copper those nets have outside the PCA
    # body is the two lanes beside the D1 Mini, too narrow for a pad; probe
    # them on U2's header pins 9/10 (they protrude on the copper side)
    for i, (net, x) in enumerate((("+12V", 50.8), ("+5V", 63.5), ("+3V3", 76.2), ("RAIL_ADC", 88.9),
                                  ("GND", 101.6), ("GND", 114.3)), 1):
        tp = comp("Connector", "TestPoint", f"TP{i}", net, x, 190.5,
                  footprint="carrier:TestPoint_THT_D2.2_1.181", ref_off=(0, -5.08), val_off=(0, -2.54))
        wire(tp["1"], (x, 195.58)); glabel(net, (x, 195.58), 0)

    # --- rack standoff holes, netlist-managed so F8 keeps them
    for i in range(1, 5):
        comp("Mechanical", "MountingHole", f"H{i}", "M3 rack standoff", 254 + 15.24 * i, 190.5,
             footprint="carrier:MountingHole_M3_3.175", ref_off=(0, -5.08), val_off=(0, 5.08))

    note("Animatronic eyes carrier: D1 Mini ESP32 + PCA9685 + LM2596 on one milled board, "
         "M3 standoffs into the rack.\\n"
         "Power: 12 V pigtail -> J1 -> LM2596 (set 5.0-5.1 V unloaded, USB unplugged) -> +5V.\\n"
         "+5V is star-routed on the board: separate traces from U3 OUT+ to U2 V+ and to U1 VCC (pin 35).\\n"
         "C1/C2 hang on the +5V run to U1 pin 35. R1/R2 divide the PCA V+ rail to GPIO36 (ADC1_CH0) for the rail monitor (Rail.cpp PIN=36, DIVIDER=2).\\n"
         "U2 rows are internally paralleled (jumper pad groups on the footprint): +5V feeds the right V+ from the buck and the left V+ feeds the divider.\\n"
         "I2C is on IO25 (SDA) / IO27 (SCL), not 21/22: single-sided routing can only reach the OUTER header columns. Wire.begin(25, 27).\\n"
         "U1 pin numbers = header positions per r0oland ESP32_mini; VERIFY against the board silk before cutting.",
         (38.1, 215.9), 1.6)


def write(outdir):
    build()
    libs = []
    for (lib, name) in used:
        if lib == "carrier":
            libs.append(custom[name][0])
        else:
            blk = sexp.dump(libsym(lib, name), indent=2)
            libs.append(blk.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1))
    doc = ["(kicad_sch", "\t(version 20260306)", '\t(generator "eeschema")', '\t(generator_version "10.0")',
           f'\t(uuid "{SHEET}")', '\t(paper "A3")', "\t(title_block",
           '\t\t(title "Animatronic eyes carrier")', '\t\t(date "2026-09-25")', '\t\t(rev "V1")',
           '\t\t(company "SLN")', '\t\t(comment 1 "D1 Mini ESP32 + PCA9685 + LM2596, milled single-sided")',
           "\t)", "\t(lib_symbols", "\n".join(libs), "\t)", "\n".join(items),
           "\t(sheet_instances", '\t\t(path "/"', '\t\t\t(page "1")', "\t\t)", "\t)",
           "\t(embedded_fonts no)", ")"]
    os.makedirs(outdir, exist_ok=True)
    open(f"{outdir}/{PROJECT}.kicad_sch", "w").write("\n".join(doc) + "\n")
    print(f"wrote {outdir}/{PROJECT}.kicad_sch")


if __name__ == "__main__":
    write(sys.argv[1] if len(sys.argv) > 1 else ".")
