#!/bin/sh
set -e

log_info() {
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${BLUE}[rules]${NC}: ${BOLD}$1${NC}"
}

set -- left right switch_plate switch_plate_without_mcu_cutout bottom_board_empty bottom_board_with_tenting_puck

for BOARD in "$@"; do
    log_info "Adding JLCPCB design rules: $BOARD"
    cp kicad/JLCPCB.kicad_dru "out/novum/pcbs/$BOARD.kicad_dru"
    $DOCKER_CMD ./kicad/add_rules.py "out/novum/pcbs/$BOARD.kicad_pcb"
done
