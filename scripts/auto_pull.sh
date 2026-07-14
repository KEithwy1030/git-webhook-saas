#!/bin/bash
# AI GitOps Auto-Pull script for git-webhook-saas
# This script runs on the VPS via cron every minute to automatically sync with GitHub.

cd /opt/git-webhook-saas

# Fetch latest references from GitHub
git fetch origin master > /dev/null 2>&1

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u})

# If remote commit differs, pull and reload the app container
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] 🚀 New updates found on GitHub. Upgrading..."
    git pull origin master
    
    # Restart the application container to load new source code
    docker compose restart app
    echo "[$(date)] ✅ Upgrade finished. Application container reloaded."
fi
