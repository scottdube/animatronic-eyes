"""Footprints for the eyes carrier, emitted as KiCad 10 .kicad_mod text.

Every through-hole pad is drawn for the shop's bit set: drill values are the
bits themselves (0.813 / 1.181 / 1.588 / 3.175 mm) so pcbmill's nearest-bit
snap is a no-op and the 0.25 mm annulus gate is met by construction.
Module pads are 1.78 mm on a 1.181 mm drill = 0.30 mm annulus, the same
geometry as the proven NodeMCU-32S footprint in sln-geo-aux-heat.
"""
import uuid as uuidlib

NS = uuidlib.UUID("a11e5c0d-0000-4000-8000-0000000000e7")
_n = [0]


def uid():
    _n[0] += 1
    return str(uuidlib.uuid5(NS, "fp" + str(_n[0])))


PAD_D = 1.78          # module / header pad diameter
DRILL = 1.181         # the bit
NPTH = 1.181          # pin passes through, no copper


def pad(num, x, y, size=PAD_D, drill=DRILL, shape="circle", npth=False,
        rect=False, solid=False):
    """solid=True: pour connects without thermal relief (servo/buck GND return
    pins - a 0.5 mm spoke is a 0.5 mm trace, and the keepout at H3/H4 leaves
    the PCA's GND pins one spoke).  Everything else keeps reliefs for soldering."""
    if npth:
        return (f'\t(pad "" np_thru_hole circle\n\t\t(at {x} {y})\n'
                f'\t\t(size {drill} {drill})\n\t\t(drill {drill})\n'
                f'\t\t(layers "*.Cu" "*.Mask")\n\t\t(uuid "{uid()}")\n\t)')
    shp = "rect" if rect else shape
    return (f'\t(pad "{num}" thru_hole {shp}\n\t\t(at {x} {y})\n'
            f'\t\t(size {size} {size})\n\t\t(drill {drill})\n'
            f'\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n'
            f'\t\t(thermal_bridge_angle 90)\n'   # KiCad defaults round pads to 45, whose spokes land on the sliver between 2x2 pads
            + ('\t\t(zone_connect 2)\n' if solid else '')
            + f'\t\t(uuid "{uid()}")\n\t)')


def line(x1, y1, x2, y2, layer, w=0.12):
    return (f'\t(fp_line\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(layer "{layer}")\n\t\t(uuid "{uid()}")\n\t)')


def rect(x1, y1, x2, y2, layer, w=0.12):
    return "\n".join([line(x1, y1, x2, y1, layer, w), line(x2, y1, x2, y2, layer, w),
                      line(x2, y2, x1, y2, layer, w), line(x1, y2, x1, y1, layer, w)])


def text(kind, s, x, y, layer, size=1.0, hide=False):
    h = "\n\t\t(hide yes)" if hide else ""
    if kind in ("Reference", "Value"):
        return (f'\t(property "{kind}" "{s}"\n\t\t(at {x} {y} 0)\n'
                f'\t\t(layer "{layer}"){h}\n\t\t(uuid "{uid()}")\n'
                f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n'
                f'\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)')
    return (f'\t(fp_text user "{s}"\n\t\t(at {x} {y} 0)\n\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{uid()}")\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n'
            f'\t\t)\n\t)')


# 3D models.  D1 Mini + LM2596 are the ratgdo project's files (my-rat-ratgdo/
# kicad_files/D1 Mini - ESP32/3dmodels) with ratgdo's tuned offsets - both
# footprints here share ratgdo's pad frame.  ratgdo's D1 file ("+ MF") is the
# module on male headers plugged into 8.5 mm female sockets; this board
# solders the male headers straight in (Scott), so D1_Mini_ESP32_male.stp is
# that file with the socket geometry unlinked (the SHAPE_REPRESENTATION_
# RELATIONSHIP #38 line deleted - the two socket occurrences stay in the
# assembly but carry no solid) and the model dropped 8.5 so the male header
# plastic sits on the carrier.  PCA9685.step is a GrabCAD-style
# model (author 'antoi', 2022; Scott's Downloads/16-channel-i2c-servo-
# controller-1).  Its raw CARTESIAN_POINTs lie flat, but the assembly
# placement stands the board on edge, so the frame was found by rendering:
# rotate (-90,0,180) lays it flat with the servo field toward +y, and the
# offset then puts its mounting holes on H3/H4 (KiCad applies the offset in
# the board frame AFTER the rotation).  z 2.54 = header plastic; the real
# height is the H3/H4 standoff, Scott's call.  Its servo-pin tails hang
# 10 mm below its PCB in the model - that is the model, not the part.  The stock Phoenix
# MKDS model has its wire entry on the footprint's +y side; KF301 here has it
# on -y, hence the 180 + 5.08 offset.  Verified 2026-09-26 by rendering.
STOCK3D = "${KICAD10_3DMODEL_DIR}"
PROJ3D = "${KIPRJMOD}/3dmodels"


def model(path, offset=(0, 0, 0), rotate=(0, 0, 0), scale=(1, 1, 1)):
    """3D model block. Offsets are in the footprint's own frame (mm), rotation
    in degrees; KiCad applies the footprint's placement on top."""
    xyz = lambda v: f"(xyz {v[0]:g} {v[1]:g} {v[2]:g})"
    return (f'\t(model "{path}"\n\t\t(offset\n\t\t\t{xyz(offset)}\n\t\t)\n'
            f'\t\t(scale\n\t\t\t{xyz(scale)}\n\t\t)\n\t\t(rotate\n\t\t\t{xyz(rotate)}\n\t\t)\n\t)')


def footprint(name, descr, body, ref_at=(0, 0), val_at=(0, 2), jumpers=(), models=()):
    head = [f'(footprint "{name}"', "\t(version 20241229)", '\t(generator "gen_carrier")',
            '\t(generator_version "10.0")', '\t(layer "F.Cu")', f'\t(descr "{descr}")',
            text("Reference", "REF**", *ref_at, "F.SilkS"),
            text("Value", name, *val_at, "F.Fab"),
            text("Datasheet", "", 0, 0, "F.Fab", hide=True).replace("fp_text user", 'property "Datasheet"'),
            ]
    # Datasheet/Description as proper hidden properties
    head = head[:-1] + [
        f'\t(property "Datasheet" ""\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n\t\t(hide yes)\n'
        f'\t\t(uuid "{uid()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t)\n\t)',
        f'\t(property "Description" "{descr}"\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n\t\t(hide yes)\n'
        f'\t\t(uuid "{uid()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t)\n\t)',
        '\t(attr through_hole)',
    ]
    if jumpers:   # pads the MODULE ties together; DRC then treats them as connected
        head.append('\t(jumper_pad_groups ' + " ".join(
            "(" + " ".join(f'"{p}"' for p in g) + ")" for g in jumpers) + ')')
    return "\n".join(head + body + ["\t(embedded_fonts no)"] + list(models) + [")"]) + "\n"


# ------------------------------------------------------------ D1 Mini ESP32
# Geometry from r0oland/ESP32_mini_KiCad_Library (the footprint the ratgdo
# board uses): four pin columns at x = +/-11.43 and +/-13.97, ten rows at
# y = -11.43 .. 11.43, USB end at +y, antenna end at -y.  Pad numbers are
# HEADER POSITIONS (1-20 left side, odd = outer column; 21-40 right side,
# odd = inner column) and match ESP32_mini.kicad_sym.
# Flash-bus positions (SD0/SD1/SD2/SD3/CLK/CMD) and TD0 are NPTH.
D1_FLASH = {17, 19, 20, 37, 38, 39, 40}
D1_NAMES = {1: "GND", 2: "RST", 3: "NC", 4: "IO36", 5: "IO39", 6: "IO26", 7: "IO35",
            8: "IO18", 9: "IO33", 10: "IO19", 11: "IO34", 12: "IO23", 13: "IO14",
            14: "IO5", 15: "NC", 16: "3V3", 17: "SD2", 18: "IO13", 19: "CMD",
            20: "SD3", 21: "TXD", 22: "GND", 23: "RXD", 24: "IO27", 25: "SCL",
            26: "IO25", 27: "SDA", 28: "IO32", 29: "IO17", 30: "IO12", 31: "IO16",
            32: "IO4", 33: "GND", 34: "IO0", 35: "VCC", 36: "IO2", 37: "TD0",
            38: "SD1", 39: "SD0", 40: "CLK"}


def d1_pad_xy(n):
    if n <= 20:
        row = (n - 1) // 2
        x = -13.97 if n % 2 == 1 else -11.43
    else:
        row = (n - 21) // 2
        x = 11.43 if n % 2 == 1 else 13.97
    return x, round(-11.43 + 2.54 * row, 2)


def d1_mini_esp32():
    body = []
    for n in range(1, 41):
        x, y = d1_pad_xy(n)
        body.append(pad(n, x, y, npth=(n in D1_FLASH)))
    # module PCB 31.4 x 36.8 (silk), USB-C tab beyond +y
    # silk: only the part of the module that sits over board (top end and USB
    # tab overhang the notch / bottom edge on the carrier); full body on F.Fab
    body.append(rect(-15.7, -13.6, 15.7, 17.5, "F.SilkS"))
    body.append(rect(-4.5, 17.78, 4.5, 24.13, "F.Fab", 0.1))
    # courtyard as ONE closed polyline (two rects sharing an edge is "self-intersecting" to DRC)
    cy = [(-16.0, -19.3), (16.0, -19.3), (16.0, 18.0), (4.8, 18.0), (4.8, 24.4),
          (-4.8, 24.4), (-4.8, 18.0), (-16.0, 18.0)]
    for (x1, y1), (x2, y2) in zip(cy, cy[1:] + cy[:1]):
        body.append(line(x1, y1, x2, y2, "F.CrtYd", 0.05))
    body.append(rect(-15.7, -19.05, 15.7, 17.78, "F.Fab", 0.1))
    body.append(text("user", "USB-C", 0, 21.0, "F.Fab", 0.8))
    body.append(text("user", "ANTENNA - NO COPPER", 0, -15.5, "F.Fab", 0.8))
    body.append(text("user", "1", -16.8, -11.43, "F.SilkS", 0.8))
    body.append(text("user", "22", 16.9, -11.43, "F.SilkS", 0.8))
    return footprint("D1_Mini_ESP32_THT", "D1 Mini ESP32 (WROOM-32), 40-pin, 1.78/1.181 pads, flash pins NPTH",
                     body, ref_at=(18.4, 0), val_at=(0, 0), jumpers=[("1", "22", "33")],
                     models=[model(PROJ3D + "/D1_Mini_ESP32_male.stp", (-0.5, -0.5, -8.5), (0, 0, -90))])


# ------------------------------------------------------------ LM2596 module
# From ratgdo_custom.pretty/LM2596: 17.6 x 39.8 mm pin grid, pad 1 IN+ (rect),
# 2 IN-, 3 OUT+, 4 OUT-.  Board ~43 x 21 mm; silk drawn as the ratgdo file did.
def lm2596():
    body = [pad(1, 17.6, 0, size=2.4, drill=1.181, rect=True),
            pad(2, 0, 0, size=2.4, drill=1.181, solid=True),      # IN-  (GND, full buck current)
            pad(3, 17.6, 39.8, size=2.4, drill=1.181),
            pad(4, 0, 39.8, size=2.4, drill=1.181, solid=True),   # OUT- (GND, full 5 V return)
            rect(-1.7, -1.6, 19.3, 41.4, "F.SilkS"),      # 21 x 43 body
            rect(-2.0, -1.9, 19.6, 41.7, "F.CrtYd", 0.05),
            rect(-1.7, -1.6, 19.3, 41.4, "F.Fab", 0.1),
            text("user", "IN+", 17.6, 2.4, "F.SilkS", 0.8),
            text("user", "IN-", 0, 2.4, "F.SilkS", 0.8),
            text("user", "OUT+", 17.6, 37.4, "F.SilkS", 0.8),
            text("user", "OUT-", 0, 37.4, "F.SilkS", 0.8)]
    return footprint("LM2596_Module", "LM2596 buck module, 4 pins 17.6 x 39.8 mm (ratgdo footprint, NOT caliper-verified)",
                     body, ref_at=(8.8, 20), val_at=(8.8, 30),
                     models=[model(PROJ3D + "/LM2596.step", (-1.25, 2, 2.5), (0, 0, 90))])


# ------------------------------------------------------------ PCA9685 module
# Adafruit 'PCA9685 rev C' Eagle board (github adafruit/Adafruit-16-Channel-
# PWM-Servo-Driver-PCB): body 62.23 x 25.4, corner radius 3.175, two 1x06 rows
# 58.42 mm apart, pins 2.54 pitch. Pin order along a row, from the SERVO edge:
# 1 V+ (5.0V), 2 VCC, 3 SDA, 4 SCL, 5 OE, 6 GND.  Footprint origin = body
# centre; servo headers toward +y; pads 1-6 left row, 7-12 right row.
# Clone assumed identical: CHECK WITH CALIPERS before cutting.
PCA_ROW_X = 29.21
PCA_PIN_Y = [6.223, 3.683, 1.143, -1.397, -3.937, -6.477]   # pads 1..6
PCA_NAMES = ["V+", "VCC", "SDA", "SCL", "OE", "GND"]


def pca9685():
    body = []
    for i, y in enumerate(PCA_PIN_Y):
        body.append(pad(i + 1, -PCA_ROW_X, y, solid=(i == 5)))   # pin 6/12 = GND, servo return
        body.append(pad(i + 7, PCA_ROW_X, y, solid=(i == 5)))
    # body outline sits on the board edge (top) and crosses the notch (bottom),
    # so silk is corner ticks on the wings only; the full outline is on F.Fab
    for sx in (-1, 1):
        for sy, y0 in ((-1, -12.2), (1, 11.6)):   # bottom ticks pulled in: body overhangs the edge 0.5
            body.append(line(sx * 31.115, y0, sx * 31.115, y0 - sy * 2.5, "F.SilkS"))
            body.append(line(sx * 31.115, y0, sx * (31.115 - 2.5), y0, "F.SilkS"))
    # courtyard = the two header rows only.  The module rides on H3/H4 (its own
    # holes line up with the carrier's, Scott 2026-09-25) and on its headers, so
    # the carrier area under its body is free for anything under the header
    # height; a full-body courtyard would also collide with H3/H4 by design.
    for sx in (-1, 1):
        body.append(rect(sx * (PCA_ROW_X - 1.5), -7.6, sx * (PCA_ROW_X + 1.5), 7.4, "F.CrtYd", 0.05))
    # its mounting holes, drawn for the record (the carrier's H3/H4 sit here)
    for hx in (-28.471, 28.471):
        body.append(f'\t(fp_circle\n\t\t(center {hx} -9.525)\n\t\t(end {hx + 1.6} -9.525)\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "F.Fab")\n\t\t(uuid "{uid()}")\n\t)')
    body.append(text("user", "holes = carrier H3/H4", 0, -11.0, "F.Fab", 0.8))
    body.append(rect(-31.115, -12.7, 31.115, 12.7, "F.Fab", 0.1))
    # servo pin field 16 x 3, 2.54 pitch, x -24.13..24.13, y 6.22..11.30
    body.append(rect(-25.4, 5.0, 25.4, 12.5, "F.Fab", 0.1))
    body.append(text("user", "SERVO HEADERS 16x3", 0, 8.8, "F.Fab", 0.8))
    body.append(text("user", "V+ terminal", 0, -8.9, "F.Fab", 0.8))
    for i, nm in enumerate(PCA_NAMES):
        body.append(text("user", nm, -PCA_ROW_X + 3.0, PCA_PIN_Y[i], "F.SilkS", 0.8))
        body.append(text("user", nm, PCA_ROW_X - 3.0, PCA_PIN_Y[i], "F.SilkS", 0.8))
    return footprint("PCA9685_Adafruit_Module", "PCA9685 16ch servo board (Adafruit rev C geometry), 2x 1x06 rows 58.42 mm apart, body 62.23 x 25.4",
                     body, ref_at=(-34, 0), val_at=(0, 0),
                     jumpers=[(str(i + 1), str(i + 7)) for i in range(6)],
                     models=[model(PROJ3D + "/PCA9685.step", (-0.18, -0.36, 2.54), (-90, 0, 180))])


# ------------------------------------------------------------ small parts
def mounting_hole_m3():
    # no courtyard: H3/H4 sit inside the PCA's header-row geometry on purpose, and
    # the copper guard is the board rule area, not this footprint
    # no silk ring either: at H3/H4 a 3.25 ring lands on the PCA's GND pads
    body = [pad("", 0, 0, drill=3.175, npth=True)]
    return footprint("MountingHole_M3_3.175", "M3 rack standoff hole, drilled 3.175 (the bit), NPTH; pour keepout is a board rule area",
                     body, ref_at=(0, -4.2), val_at=(0, 4.2))


def testpoint():
    body = [pad(1, 0, 0, size=2.2, drill=1.181),
            f'\t(fp_circle\n\t\t(center 0 0)\n\t\t(end 1.5 0)\n\t\t(stroke\n\t\t\t(width 0.12)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "F.SilkS")\n\t\t(uuid "{uid()}")\n\t)']
    return footprint("TestPoint_THT_D2.2_1.181", "Drilled test point, 2.2 pad on the 1.181 bit (0.51 annulus)",
                     body, ref_at=(0, -2.4), val_at=(0, 2.4),
                     models=[model(STOCK3D + "/TestPoint.3dshapes/TestPoint_Loop_D2.50mm_Drill1.0mm.step")])


def kf301_2p():
    """KF301 5.08 mm 2-position screw terminal (InvenTree #291). Pins 5.08 apart,
    body 10.2 x 7.6, wire entry on the -y side."""
    body = [pad(1, 0, 0, size=2.6, drill=1.181, rect=True),
            pad(2, 5.08, 0, size=2.6, drill=1.181, solid=True),   # GND: the whole 12 V return, same as the buck IN-
            rect(-2.54, -4.1, 7.62, 3.5, "F.SilkS"),
            rect(-2.8, -4.4, 7.9, 3.8, "F.CrtYd", 0.05),
            rect(-2.54, -4.1, 7.62, 3.5, "F.Fab", 0.1),
            # labels and ref inside the body: on the carrier the wire-entry face points at the PCA (back of the box)
            text("user", "12V", 0, 2.4, "F.SilkS", 0.8),
            text("user", "GND", 5.08, 2.4, "F.SilkS", 0.8)]
    return footprint("KF301_1x02_P5.08", "KF301-5.0 screw terminal 2P 5.08 mm, pads 2.6/1.181",
                     body, ref_at=(2.54, -2.4), val_at=(2.54, 0),
                     models=[model(STOCK3D + "/TerminalBlock_Phoenix.3dshapes/TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal.step", (5.08, 0, 0), (0, 0, 180))])


def r_axial_p10():
    body = [pad(1, 0, 0, size=1.78, drill=1.181), pad(2, 10.16, 0, size=1.78, drill=1.181),
            line(1.4, 0, 1.9, 0, "F.SilkS"), line(8.26, 0, 8.76, 0, "F.SilkS"),
            rect(1.9, -1.25, 8.26, 1.25, "F.SilkS"),
            rect(-1.2, -1.5, 11.36, 1.5, "F.CrtYd", 0.05),
            rect(1.9, -1.25, 8.26, 1.25, "F.Fab", 0.1)]
    return footprint("R_Axial_P10.16", "1/4 W axial resistor, 10.16 mm pitch, pads 1.78/1.181",
                     body, ref_at=(5.08, -2.4), val_at=(5.08, 0),
                     models=[model(STOCK3D + "/Resistor_THT.3dshapes/R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal.step")])


def cp_radial_d6_3():
    import math
    ring = [(1.25 + 3.4 * math.cos(2 * math.pi * i / 24), 3.4 * math.sin(2 * math.pi * i / 24)) for i in range(24)]
    body = [pad(1, 0, 0, size=1.9, drill=1.181, rect=True), pad(2, 2.5, 0, size=1.9, drill=1.181)]
    body += [line(round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3), "F.SilkS")
             for a, b in zip(ring, ring[1:] + ring[:1])]
    body += [
            f'\t(fp_circle\n\t\t(center 1.25 0)\n\t\t(end 3.6 0)\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "F.CrtYd")\n\t\t(uuid "{uid()}")\n\t)',
            text("user", "+", -1.6, -2.6, "F.SilkS", 0.9)]
    return footprint("CP_Radial_D6.3_P2.5", "220 uF radial electrolytic, 6.3 dia, 2.5 pitch, pin 1 = +",
                     body, ref_at=(1.25, -4.4), val_at=(1.25, 4.4),
                     models=[model(STOCK3D + "/Capacitor_THT.3dshapes/CP_Radial_D6.3mm_P2.50mm.step")])


def c_disc_p5():
    body = [pad(1, 0, 0, size=1.78, drill=1.181), pad(2, 5.08, 0, size=1.78, drill=1.181),
            rect(1.3, -1.4, 3.78, 1.4, "F.SilkS"),
            rect(-1.2, -1.7, 6.3, 1.7, "F.CrtYd", 0.05),
            rect(-0.6, -1.4, 5.7, 1.4, "F.Fab", 0.1)]
    return footprint("C_Disc_P5.08", "100 nF ceramic disc/MLCC, 5.08 mm pitch (0.1 in leads)",
                     body, ref_at=(2.54, -2.5), val_at=(2.54, 0),
                     models=[model(STOCK3D + "/Capacitor_THT.3dshapes/C_Disc_D6.0mm_W2.5mm_P5.00mm.step")])


ALL = {"D1_Mini_ESP32_THT": d1_mini_esp32, "LM2596_Module": lm2596,
       "PCA9685_Adafruit_Module": pca9685, "MountingHole_M3_3.175": mounting_hole_m3,
       "TestPoint_THT_D2.2_1.181": testpoint, "KF301_1x02_P5.08": kf301_2p,
       "R_Axial_P10.16": r_axial_p10, "CP_Radial_D6.3_P2.5": cp_radial_d6_3,
       "C_Disc_P5.08": c_disc_p5}


def write_lib(outdir):
    import os
    os.makedirs(outdir, exist_ok=True)
    for name, fn in ALL.items():
        _n[0] = 0            # deterministic uuids per footprint
        open(f"{outdir}/{name}.kicad_mod", "w").write(fn())
    return list(ALL)


if __name__ == "__main__":
    import sys
    print(write_lib(sys.argv[1] if len(sys.argv) > 1 else "carrier.pretty"))
