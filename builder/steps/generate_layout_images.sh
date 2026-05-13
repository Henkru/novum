#!/bin/sh
set -e

log_info() {
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${BLUE}[layout]${NC}: ${BOLD}$1${NC}"
}

REV=rev2
set -- default vial

mkdir -p out/novum/layout
for KEYMAP in "$@"; do
    log_info "Generating layout image for: ${REV}:${KEYMAP}"
    OUT=$(mktemp)
    keymap parse -c 10 -q "novum/qmk/${REV}/keymaps/${KEYMAP}/keymap.json" -o "$OUT"
    keymap draw -j "novum/qmk/${REV}/keyboard.json" "$OUT" > "out/novum/layout/${REV}_${KEYMAP}.svg"
done
