#!/usr/bin/env bash
# Deploy script: run on the Azure server to pull the latest code and rebuild.
# Usage: bash deploy.sh
set -euo pipefail   # stop on the first error

echo "==> Pulling latest code from GitHub"
git pull

echo "==> Rebuilding and restarting containers"
docker compose -f compose.prod.yml --env-file .env.prod up --build -d

echo "==> Removing old unused images to save disk space"
docker image prune -f

echo "==> Container status"
docker compose -f compose.prod.yml --env-file .env.prod ps