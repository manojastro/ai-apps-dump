#!/usr/bin/env bash
# Helpdesk Anywhere — Ubuntu deployment host only.
# Executes on the Ubuntu VM (deployment/hosting target).
# Windows dev machine never runs this except for review.
set -euo pipefail

# Requires: Docker Engine + Compose plugin, .env with PUBLIC_HOST set.
if [[ ! -f .env ]]; then
  echo "Missing .env (copy from .env.example and set PUBLIC_HOST)" >&2
  exit 1
fi

docker compose up -d --build
docker compose ps
echo "Caddy will obtain Let's Encrypt certs automatically once DNS resolves."
