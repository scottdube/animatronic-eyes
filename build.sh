#!/bin/bash
# Build EyeMech_PS4 and flash it.
#   ./build.sh            compile only -> build/EyeMech_PS4.ino.bin
#   ./build.sh ota [HOST] compile, then upload over Wi-Fi (default host: 192.168.30.211)
#   ./build.sh usb        compile, then flash over USB (keeps NVS, so the controller bond survives)
# Either flash restarts the board, which drops the controller: hold P4 ~10 s, then press P4.
set -euo pipefail
cd "$(dirname "$0")"
CLI="/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"
CFG="$HOME/.arduinoIDE/arduino-cli.yaml"
FQBN="esp32:esp32:esp32:PartitionScheme=min_spiffs"  # two 1.875 MB app slots; NVS unchanged
SKETCH=firmware/EyeMech_PS4
BIN=build/EyeMech_PS4.ino.bin

printf '#define BUILD_ID "%s"\n' "$(git describe --always --dirty)" > "$SKETCH/build_id.h"
"$CLI" compile --fqbn "$FQBN" --config-file "$CFG" --output-dir build "$SKETCH" | grep -E 'Sketch uses|Global'

case "${1:-}" in
  ota)
    host="${2:-192.168.30.211}"
    # A flash restarts the board and drops live values: refuse while the page has unsaved
    # changes (FORCE=1 to flash anyway). Added 2026-09-25 after a flash went out unchecked.
    if curl -s --max-time 5 "http://$host/values" | grep -q '"dirty":true' && [ "${FORCE:-}" != 1 ]; then
      echo "Unsaved changes on the eyes: Save (or Revert) on the page first, or FORCE=1 $0 ota" >&2
      exit 3
    fi
    curl -sS --max-time 180 -F "firmware=@$BIN" "http://$host/update"
    ;;
  usb)
    "$CLI" upload --fqbn "$FQBN,UploadSpeed=115200,EraseFlash=none" --config-file "$CFG" \
      -p /dev/cu.usbserial-0001 --input-dir build "$SKETCH" | grep -E 'Hash of data|rror'
    ;;
  "") ;;
  *) echo "usage: $0 [ota [host] | usb]" >&2; exit 2 ;;
esac
