#!/bin/sh
set -e

log_info() {
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${BLUE}[generate]${NC}: ${BOLD}$1${NC}"
}

if [ -z "${NOVUM_VERSION}" ]; then
    GIT_HASH=$(git rev-parse --short HEAD || true)
    GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD || true)
    NOVUM_VERSION="${GIT_BRANCH}-${GIT_HASH}"
    if [ -z "${NOVUM_VERSION}" ]; then
        NOVUM_VERSION=""
    fi
fi

log_info "Installing depedencies"
npm install

log_info "Genarating unrouted PCBs"
npm run update-artwork
NOVUM_VERSION=$NOVUM_VERSION npm run generate
