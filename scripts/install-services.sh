#!/bin/bash
# Chicken Coop Service Installation Script.
# Detects coop identity from hostname, creates a Python virtual environment,
# installs pip dependencies, configures the systemd service, and secures
# IoT certificate files.
#
# Usage: ./install-services.sh
# Must be run from within the project directory.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_NAME="chickencoop-monitor"  # chickencoop-v2 service name
SERVICE_FILE="$PROJECT_DIR/config/systemd/${SERVICE_NAME}.service"

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

# Create Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv "$PROJECT_DIR/venv"
source "$PROJECT_DIR/venv/bin/activate"

# Install pip dependencies
echo "Installing pip requirements..."
pip install -r "$PROJECT_DIR/requirements.txt"

# Copy service file to systemd
sudo cp "$SERVICE_FILE" /etc/systemd/system/${SERVICE_NAME}.service

# Update COOP_ID in installed service file
sudo sed -i "s/COOP_ID=.*/COOP_ID=$COOP_ID\"/" /etc/systemd/system/${SERVICE_NAME}.service

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service for auto-start on boot
sudo systemctl enable ${SERVICE_NAME}

# Secure IoT certificates
CERT_DIR="$PROJECT_DIR/certs"
if [ -d "$CERT_DIR" ]; then
    echo "Securing certificate files..."
    chmod 600 "$CERT_DIR"/*.pem 2>/dev/null || true
    chmod 600 "$CERT_DIR"/*-private.pem.key 2>/dev/null || true
fi

echo "Service installed successfully!"
echo "Run 'sudo systemctl start ${SERVICE_NAME}' to start the service"
