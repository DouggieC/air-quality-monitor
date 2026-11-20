#!/bin/bash

APP_DIR="/home/doug/apps/air-quality-monitor"
PYTHON="$APP_DIR/.venv/bin/python"

# Get environment variables
set -a
source ${APP_DIR}/.env
set +a

echo "Starting MLflow backfill"
$PYTHON ${APP_DIR}/scripts/backfill_mlflow.py
echo "Finished MLflow backfill"
