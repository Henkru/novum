#!/bin/sh
set -e

ensure_qmk_deps() {
    if ! command -v qmk >/dev/null 2>&1; then
        return
    fi

    if qmk hello >/dev/null 2>&1; then
        return
    fi

    if [ -n "$QMK_PYTHON" ]; then
        PYTHON="$QMK_PYTHON"
    elif [ -x /opt/uv/tools/qmk/bin/python3 ]; then
        PYTHON=/opt/uv/tools/qmk/bin/python3
    else
        PYTHON=python3
    fi

    echo "[vial]: Installing QMK Python dependencies"
    "$PYTHON" -m pip install -r requirements.txt
    qmk hello >/dev/null
}

ensure_rp2040_submodules() {
    if ! command -v git >/dev/null 2>&1; then
        return
    fi

    if [ -f lib/chibios/os/common/startup/ARMCMx/compilers/GCC/mk/startup_rp2040.mk ] \
        && [ -d lib/chibios-contrib/os/hal/ports/RP/RP2040 ] \
        && [ -d lib/pico-sdk/src/rp2_common ]; then
        return
    fi

    echo "[vial]: Updating RP2040 firmware submodules"
    git submodule update --init --recursive --checkout --force lib/chibios lib/chibios-contrib lib/pico-sdk
}

rm -rf external/vial-qmk/keyboards/novum
mkdir -p external/vial-qmk/keyboards/novum
cp -R novum/qmk/. external/vial-qmk/keyboards/novum
cd external/vial-qmk || exit 1
ensure_qmk_deps
ensure_rp2040_submodules
make novum/rev2:vial

mkdir -p ../../out/novum/fw
cp  .build/novum_rev2_vial.uf2 ../../out/novum/fw
