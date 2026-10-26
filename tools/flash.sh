#!/usr/bin/env bash
# Linux counterpart of flash.ps1: wait for the RP2040 boot drive (label RPI-RP2), copy the firmware.
# Usage: tools/flash.sh [build/lily58_rev1_tokimen.uf2] [timeout_sec]
set -euo pipefail

UF2=${1:-$(dirname "$0")/../build/lily58_rev1_tokimen.uf2}
TIMEOUT=${2:-120}
DEV=/dev/disk/by-label/RPI-RP2

echo "waiting for RPI-RP2: plug USB into the half to flash and press reset"
for ((i = 0; i < TIMEOUT * 2; i++)); do
    [ -e "$DEV" ] && break
    sleep 0.5
done
[ -e "$DEV" ] || { echo "timeout: RPI-RP2 did not appear in $TIMEOUT s" >&2; exit 1; }

# use the automount if a desktop service already mounted it, otherwise mount via udisks
MNT=$(findmnt -n -o TARGET --source "$(readlink -f "$DEV")" || true)
if [ -z "$MNT" ]; then
    udisksctl mount -b "$DEV" >/dev/null
    MNT=$(findmnt -n -o TARGET --source "$(readlink -f "$DEV")")
fi

cp "$UF2" "$MNT/"
sync
echo "copied $(basename "$UF2") to $MNT at $(date +%T)"
