#!/usr/bin/env bash
# capture-fixtures.sh - Snapshot every command the Python port shells out to,
# plus its rendered output in every format. Run this on a real Mac. The output
# is consumed by the Go and Rust ports as fixtures (replay mode) and by the
# byte-parity tests as golden outputs.
#
# Usage:
#   ./scripts/capture-fixtures.sh             # writes to tests/fixtures/local/
#   ./scripts/capture-fixtures.sh /tmp/fx     # writes to /tmp/fx
#
# Each fixture file is named after the command + args, joined with "__", with
# "/" and " " replaced by "_". Both ports compute the same key.

set -euo pipefail

OUT="${1:-$(dirname "$0")/../tests/fixtures/local}"
mkdir -p "$OUT/cmd" "$OUT/golden"

key() {
  local out=""
  for part in "$@"; do
    out="${out}${out:+__}${part//\//_}"
  done
  out="${out// /_}"
  echo "$out"
}

snap() {
  local file="$OUT/cmd/$(key "$@").txt"
  echo "  -> $(basename "$file")"
  if output=$("$@" 2>/dev/null); then
    printf '%s' "$output" > "$file"
  else
    printf '' > "$file"
  fi
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "error: this script must run on macOS (uname=$(uname -s))" >&2
  exit 1
fi

echo "Capturing system_profiler JSON snapshots..."
snap system_profiler SPHardwareDataType -json
snap system_profiler SPDisplaysDataType -json
snap system_profiler SPMemoryDataType -json
snap system_profiler SPNVMeDataType -json
snap system_profiler SPSerialATADataType -json
snap system_profiler SPStorageDataType -json
snap system_profiler SPBluetoothDataType -json
snap system_profiler SPSoftwareDataType -json
snap system_profiler SPAudioDataType -json
snap system_profiler SPNetworkDataType -json
snap system_profiler SPPowerDataType -json

echo "Capturing system_profiler text snapshots..."
snap system_profiler SPHardwareDataType
snap system_profiler SPDisplaysDataType
snap system_profiler SPMemoryDataType
snap system_profiler SPNVMeDataType
snap system_profiler SPSerialATADataType
snap system_profiler SPStorageDataType
snap system_profiler SPBluetoothDataType
snap system_profiler SPAudioDataType
snap system_profiler SPPowerDataType

echo "Capturing sysctl, ioreg, pmset, network, sw_vers..."
snap sysctl -n hw.memsize
snap sysctl -n hw.model
snap sysctl -n hw.ncpu
snap sysctl -n machdep.cpu.brand_string
snap sysctl -n kern.boottime
snap ioreg -r -n AppleSmartBattery
snap ioreg -ar -k product-release-date
snap ioreg -ar -k product-release
snap ioreg -ar -k product-name
snap ioreg -ar -k target-type
snap pmset -g batt
snap pmset -g
snap networksetup -listallhardwareports
snap netstat -i
snap sw_vers -productVersion

echo "Capturing Python golden outputs (uv run about-this-mac)..."
for fmt in text json yaml markdown public simple; do
  echo "  -> $fmt"
  uv run about-this-mac --format "$fmt" > "$OUT/golden/report.$fmt.txt"
done

for raw in hardware power graphics storage memory audio network; do
  echo "  -> raw_$raw"
  uv run about-this-mac --${raw}-info > "$OUT/golden/raw_${raw}.txt" || true
done

echo
echo "Captured to: $OUT"
echo "Commit fixtures via: git add tests/fixtures/local && git commit"
