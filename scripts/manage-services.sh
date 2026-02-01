#!/bin/bash
# Chicken Coop Service Management Script
# Manages the chickencoop-monitor systemd service on Raspberry Pi devices.
# Provides start, stop, restart, status, and log-tailing operations.
#
# Usage: ./manage-services.sh [start|stop|restart|status|logs]

set -e

SERVICE_NAME="chickencoop-monitor"

case "$1" in
    start)
        sudo systemctl start "$SERVICE_NAME"
        echo "Service started"
        ;;
    stop)
        sudo systemctl stop "$SERVICE_NAME"
        echo "Service stopped"
        ;;
    restart)
        sudo systemctl restart "$SERVICE_NAME"
        echo "Service restarted"
        ;;
    status)
        sudo systemctl status "$SERVICE_NAME"
        ;;
    logs)
        sudo journalctl -u "$SERVICE_NAME" -f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
