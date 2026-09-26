#!/bin/bash
# Export carrier.kicad_pcb for the SLN shop milling pipeline (pcbmill).
#
#   ./export_for_mill.sh [outdir]      (default: ./gerbers)
#
# Settings are the shop's, from sln-ha-config docs/reference/
# shop-pcb-fabrication-guide.md §4 (same recipe as deskhack/kicad):
#   Gerber : B.Cu + Edge.Cuts, 4.6, X2 OFF, netlist attrs OFF, NOT mirrored
#            (pcbmill owns the mirror)
#   Drill  : Excellon, inch, decimal, absolute, PTH+NPTH in ONE merged file
#            (--excellon-separate-th is the flag that breaks it; omit it)
#   Legend : F.Silkscreen SVG, NOT mirrored  (component face, lasered)
#   Mask   : B.Mask SVG, MIRRORED            (copper face, lasered)
set -euo pipefail
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
HERE="$(cd "$(dirname "$0")" && pwd)"
PCB="$HERE/carrier.kicad_pcb"
OUT="${1:-$HERE/gerbers}"

if pgrep -qi kicad; then
    echo "WARNING: KiCad is running - save first, this export reads the file on disk."
fi
mkdir -p "$OUT"

# Gate: never cut a board that has not passed DRC. Errors block; warnings print.
"$CLI" pcb drc --severity-all -o "$OUT/drc.rpt" "$PCB" >/dev/null 2>&1 || true
if ! "$CLI" pcb drc --severity-error --exit-code-violations -o "$OUT/drc-errors.rpt" "$PCB" >/dev/null 2>&1; then
    echo "DRC FAILED - errors present, see $OUT/drc-errors.rpt"
    grep -oE "^\[[a-z_]+\]" "$OUT/drc-errors.rpt" | sort | uniq -c
    exit 1
fi
_live=$(awk '/^\[[a-z_]+\]/{hdr=$0; getline nxt; if (nxt !~ /\(excluded\)/) print "    " hdr}' "$OUT/drc.rpt")
if [ -n "$_live" ]; then
    echo "DRC: 0 errors, warnings NOT blocking - review before lasering:"; echo "$_live"
else
    echo "DRC clean (0 errors, 0 warnings)"
fi

"$CLI" pcb export gerbers --output "$OUT/" --layers B.Cu,Edge.Cuts \
    --no-protel-ext --no-x2 --no-netlist --precision 6 --exclude-value "$PCB" >/dev/null
echo "gerbers -> $OUT  (B.Cu, Edge.Cuts, 4.6, X2 off, no netlist attrs)"

"$CLI" pcb export drill --output "$OUT/" --format excellon --drill-origin absolute \
    --excellon-units in --excellon-zeros-format decimal --generate-map --map-format pdf "$PCB" >/dev/null
if ls "$OUT"/*-PTH.drl >/dev/null 2>&1 || ls "$OUT"/*-NPTH.drl >/dev/null 2>&1; then
    echo "ERROR: drill files came out SPLIT (PTH/NPTH). pcbmill rejects these."; exit 1
fi
echo "drill   -> $OUT  (merged PTH+NPTH, inch, decimal, absolute)"

"$CLI" pcb export svg --output "$OUT/silkscreen.svg" --layers F.Silkscreen \
    --mode-single --page-size-mode 2 --exclude-drawing-sheet "$PCB" >/dev/null
echo "legend  -> $OUT/silkscreen.svg  (F.Silkscreen, NOT mirrored)"
"$CLI" pcb export svg --output "$OUT/soldermask.svg" --layers B.Mask --mirror \
    --drill-shape-opt 0 --mode-single --page-size-mode 2 --exclude-drawing-sheet "$PCB" >/dev/null
_unmir="$(mktemp -t bmask_unmirrored).svg"
"$CLI" pcb export svg --output "$_unmir" --layers B.Mask \
    --drill-shape-opt 0 --mode-single --page-size-mode 2 --exclude-drawing-sheet "$PCB" >/dev/null
if cmp -s "$OUT/soldermask.svg" "$_unmir"; then
    rm -f "$_unmir"; echo "ERROR: --mirror had no effect on B.Mask; do NOT laser soldermask.svg"; exit 1
fi
rm -f "$_unmir"
echo "mask    -> $OUT/soldermask.svg  (B.Mask, MIRRORED, mirror verified)"
ls -1 "$OUT"
cat <<'TXT'

Next, in the mill job (NOT here):
  pcbmill new <job> --back gerbers/carrier-B_Cu.gbr --drill gerbers/carrier.drl \
      --edge gerbers/carrier-Edge_Cuts.gbr --pcb carrier.kicad_pcb
  pcbmill drill-info ; pcbmill consolidate      # bit mapping + annulus gate
  pcbmill set blank.height <in> ; pcbmill solve-offsets   (never 'frame MX MY')
  pcbmill probe-gen ; probe-import ; touchoff ; regen ; verify ; runsheet
TXT
