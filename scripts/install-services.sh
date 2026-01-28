#!/bin/bash
# Chicken Coop Service Installation Script
# Installs systemd service based on hostname

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_FILE="$PROJECT_DIR/config/systemd/chickencoop-monitor.service"

# Detect coop by hostname
HOSTNAME=$(hostname)
echo "Detected hostname: $HOSTNAME"

if [[ "$HOSTNAME" == *"coop1"* ]]; then
    COOP_ID="coop1"
elif [[ "$HOSTNAME" == *"coop2"* ]]; then
    COOP_ID="coop2"
else
    COOP_ID="unknown"
    echo "Warning: Could not determine coop from hostname"
fi

echo "Installing service for $COOP_ID..."

# Copy service file to systemd
sudo cp "$SERVICE_FILE" /etc/systemd/system/chickencoop-monitor.service

# Update COOP_ID in installed service file
sudo sed -i "s/COOP_ID=.*/COOP_ID=$COOP_ID\"/" /etc/systemd/system/chickencoop-monitor.service /etc/systemd/system/chickencoop-monitor.service

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service for auto-start on boot
sudo systemctl enable chickencoop-monitor

# Secure IoT certificates
CERT_DIR="$PROJECT_DIR/certs"
if [ -d "$CERT_DIR" ]; then
    echo "Securing certificate files..."
    chmod 600 "$CERT_DIR"/*.pem 2>/dev/null || true
    chmod 600 "$CERT_DIR"/*-private.pem.key 2>/dev/null || true
fi

echo "Service installed successfully!"
echo "Run 'sudo systemctl start chickencoop-monitor' to start the service"
