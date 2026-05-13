#!/bin/sh
set -e

log_info() {
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
    echo "${BLUE}[qmk-json]${NC}: ${BOLD}$1${NC}"
}

REV=${QMK_REV:-rev2}
LEFT_PCB=${LEFT_PCB:-out/novum/pcbs/left.kicad_pcb}
RIGHT_PCB=${RIGHT_PCB:-out/novum/pcbs/right.kicad_pcb}

log_info "Updating physical layout JSONs for: $REV"

if [ -n "$DOCKER_CMD" ]; then
    $DOCKER_CMD ./kicad/update_qmk_jsons.py --rev "$REV" --left-pcb "$LEFT_PCB" --right-pcb "$RIGHT_PCB"
elif [ -n "$KICAD_PYTHON" ]; then
    "$KICAD_PYTHON" ./kicad/update_qmk_jsons.py --rev "$REV" --left-pcb "$LEFT_PCB" --right-pcb "$RIGHT_PCB"
elif python3 -c "import pcbnew" >/dev/null 2>&1; then
    python3 ./kicad/update_qmk_jsons.py --rev "$REV" --left-pcb "$LEFT_PCB" --right-pcb "$RIGHT_PCB"
elif python -c "import pcbnew" >/dev/null 2>&1; then
    python ./kicad/update_qmk_jsons.py --rev "$REV" --left-pcb "$LEFT_PCB" --right-pcb "$RIGHT_PCB"
else
    echo "Could not find a Python interpreter with KiCad pcbnew. Set KICAD_PYTHON to KiCad's python path." >&2
    exit 1
fi
