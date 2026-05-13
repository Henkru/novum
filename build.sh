#!/bin/sh
set -e

log_info() {
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${BLUE}${TIMESTAMP}${NC}: ${BOLD}$1${NC}"
}

if [ -f /.dockerenv ]; then
    export DOCKER_CMD=""
else
    IMAGE=henkru/ergo-builder:latest
    export DOCKER_CMD="docker run --rm -it --platform linux/amd64 -v $PWD:/kicad-project $IMAGE"
    # Build the builder if does not exist
    if [ -z "$(docker images -q $IMAGE 2> /dev/null)" ]; then
        log_info "Building the builder container"
        npm run build-builder
    fi
fi

if [ ! -f "freerouting.jar" ]; then
    log_info "'freerouting.jar' does not exist. Downloading..."
    wget -O freerouting.jar https://github.com/freerouting/freerouting/releases/download/v1.9.0/freerouting-1.9.0.jar
fi

export FREEROUTING_PATH="./freerouting.jar"

log_info "Starts building"

if [ -d "out" ]; then
    log_info "Removing the 'out' directory..."
    rm -r "out"
fi

./builder/steps/generate.sh
./builder/steps/update_qmk_jsons.sh
./builder/steps/add_design_rules.sh
./builder/steps/add_tracks.sh
./builder/steps/autoroute.sh
./builder/steps/plot_gerbers_and_images.sh
./builder/steps/build_qmk.sh
./builder/steps/build_vial.sh

log_info "\033[0;32m --- All Done ---\033[0m"
