#!/usr/bin/env python3
"""Legend raster for the F1 Ultra: F.Silkscreen rendered to a 1-bit-looking PNG at
1200 dpi, canvas forced to the Edge.Cuts extents so the PNG maps 1:1 onto the board.

Why a raster and not eyes-carrier-silk.svg: KiCad's stroke-font text is ~1700 open
fill:none polylines, which Creative Space imports as hollow, doubled letters; and
profile B (blue diode, sln-ha-config shop-pcb-fabrication-guide.md section 7) is a
bitmap recipe (dot duration / power range / DPI).  Recipe from that guide, as
deskhack's export_for_mill.sh does it.

Registration: place the PNG so its bounding box equals the blue outline's bounding
box in eyes-carrier-silk.svg (same X, Y, W, H) -- the SVG is only the camera guide.
Output: eyes-carrier-legend-1200dpi.png beside this script.
"""
import re, subprocess, tempfile, pathlib, struct

HERE = pathlib.Path(__file__).resolve().parent
PCB = HERE.parent / "carrier" / "carrier.kicad_pcb"
OUT = HERE / "eyes-carrier-legend-1200dpi.png"
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
DPI = 1200

s = PCB.read_text()
xs, ys = [], []
for m in re.finditer(r"\(gr_(?:line|arc|rect|poly)\b(.*?)\(layer \"Edge\.Cuts\"\)", s, re.S):
    for x, y in re.findall(r"\((?:start|end|mid|xy) ([\d.\-]+) ([\d.\-]+)\)", m.group(1)):
        xs.append(float(x)); ys.append(float(y))
assert xs, "no Edge.Cuts geometry found"
w_mm, h_mm = max(xs) - min(xs), max(ys) - min(ys)
# Gerber Y is KiCad Y negated; gerbv's origin is the lower-left corner.
ox, oy = min(xs) / 25.4, -max(ys) / 25.4

with tempfile.TemporaryDirectory() as td:
    subprocess.run([CLI, "pcb", "export", "gerbers", "--output", td + "/", "--layers", "F.Silkscreen",
                    "--no-protel-ext", "--no-x2", "--no-netlist", "--precision", "6", str(PCB)],
                   check=True, capture_output=True)
    gbr = next(pathlib.Path(td).glob("*F_Silkscreen*"))
    subprocess.run(["gerbv", "--export=png", f"--output={OUT}", "--border=0",
                    f"--origin={ox:.5f}x{oy:.5f}", f"--window_inch={w_mm/25.4:.5f}x{h_mm/25.4:.5f}",
                    f"--dpi={DPI}", "--background=#FFFFFF", "--foreground=#000000FF", str(gbr)],
                   check=True, capture_output=True)

# Verify the artifact, not the invocation: pixel size must equal the board at DPI.
pw, ph = struct.unpack(">II", OUT.read_bytes()[16:24])
ew, eh = round(w_mm / 25.4 * DPI), round(h_mm / 25.4 * DPI)
assert abs(pw - ew) <= 2 and abs(ph - eh) <= 2, f"PNG {pw}x{ph} px, expected {ew}x{eh}"
print(f"wrote {OUT.name}  {pw}x{ph} px @ {DPI} dpi = {pw/DPI*25.4:.2f} x {ph/DPI*25.4:.2f} mm "
      f"(board {w_mm:.2f} x {h_mm:.2f} mm = {w_mm/25.4:.3f} x {h_mm/25.4:.3f} in)")
