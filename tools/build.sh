#!/usr/bin/env bash
# Build the firmware inside WSL: bash /mnt/c/dev/lily58/tools/build.sh
# The keymap folder of this repo is linked into the vial-qmk clone as keymaps/tokimen.
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
QMK=${QMK:-$HOME/keeb/vial-qmk}
VENV=${VENV:-$HOME/keeb/venv}
KM=$QMK/keyboards/lily58/rev1/keymaps/tokimen

if [ ! -L "$KM" ]; then
    rm -rf "$KM"
    ln -s "$REPO/keymap" "$KM"
fi

cd "$QMK"
PATH=$VENV/bin:$PATH make lily58/rev1:tokimen

mkdir -p "$REPO/build"
cp lily58_rev1_tokimen.uf2 "$REPO/build/"
echo "-> $REPO/build/lily58_rev1_tokimen.uf2"
