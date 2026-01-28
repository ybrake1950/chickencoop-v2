#!/bin/bash
# Auto-update script for Raspberry Pi chicken coop systems
# Handles system packages, Python dependencies, and kernel updates

set -e

DEVICE_NAME=$(hostname)
LOG_FILE="/var/log/chickencoop-update.log"

# Log a message with timestamp to both stdout and log file.
# Arguments:
#   $1 - Message to log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting auto-update on $DEVICE_NAME"

# System package updates
log "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt update -y
apt upgrade -y
apt autoremove -y

# Python dependency updates
log "Updating Python dependencies..."
if [ -f /opt/chickencoop/requirements.txt ]; then
    pip install --upgrade -r /opt/chickencoop/requirements.txt
fi

# Kernel update detection and reboot scheduling
if [ -f /var/run/reboot-required ]; then
    log "Kernel update detected, scheduling reboot for 03:00"
    shutdown -r 03:00
fi

log "Auto-update completed"
