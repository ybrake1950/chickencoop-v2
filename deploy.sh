#!/bin/bash
# Deployment script for chickencoop-v2
# Deploys updates to multiple Raspberry Pi devices via Tailscale

set -e

# Check for commit message
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh <commit message>"
    exit 1
fi

MESSAGE="$1"

echo "Starting deployment..."

# Git operations
echo "Staging changes..."
git add .

echo "Creating commit..."
git commit -m "$MESSAGE"

echo "Pushing to remote..."
git push

# Deploy to each coop
COOPS="coop1 coop2"

for COOP in $COOPS; do
    echo "Deploying to $COOP..."

    ssh "$COOP" << 'EOF'
        cd /home/pi/chickencoop-v2

        # Stash any local changes
        git stash

        # Pull latest updates
        git pull

        # Restore stashed changes
        git stash pop || true

        # Restart the service
        sudo systemctl restart chickencoop-monitor

        # Verify service is running
        sudo systemctl is-active chickencoop-monitor
EOF

    echo "Deployment to $COOP complete!"
done

echo "All deployments complete!"
