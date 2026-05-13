#!/bin/sh
set -e

log_info() {
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${BLUE}[track]${NC}: ${BOLD}$1${NC}"
}

log_error() {
    RED='\033[0;31m'
    BOLD='\033[1m'
    NC='\033[0m'
    echo "${RED}[track]${NC}: ${BOLD}$1${NC}" >&2
}

set -- left right
FAILED_BOARDS=""

for BOARD in "$@"; do
    if [ -f "novum/kicad/$BOARD.json" ]; then
        log_info "Adding hand-created tracks: $BOARD"
        if ! $DOCKER_CMD ./kicad/import_tracks.py "out/novum/pcbs/$BOARD.kicad_pcb" "novum/kicad/$BOARD.json"; then
            log_error "Failed to add hand-created tracks: $BOARD"
            FAILED_BOARDS="$FAILED_BOARDS $BOARD"
        fi
    fi
done

if [ -n "$FAILED_BOARDS" ]; then
    log_error "Continuing without imported tracks for:$FAILED_BOARDS"
fi
