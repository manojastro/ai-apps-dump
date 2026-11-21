#!/bin/sh
# Seed step: generate synthetic data and a sandbox copy on first run, then start the app.
set -e
python -m app.cli seed
exec "$@"
