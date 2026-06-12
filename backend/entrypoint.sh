#!/bin/sh
set -eu

echo "[entrypoint] Running Alembic migrations..."
python run_migration.py

export DATAVUE_SKIP_STARTUP_MIGRATIONS=1

echo "[entrypoint] Starting DataVue backend..."
exec python main.py
