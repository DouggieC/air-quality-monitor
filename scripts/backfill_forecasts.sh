#!/bin/bash

APP_DIR="/home/doug/apps/air-quality-monitor"
PYTHON="$APP_DIR/.venv/bin/python"

# Get environment variables
set -a
source ${APP_DIR}/.env
set +a

$PYTHON ${APP_DIR}/scripts/backfill_forecasts.py

echo "Sorting hourly forecasts by collected_at and forecast_for..."
{ head -n 1 ${APP_DIR}/data/hourly_forecast.csv; \
  tail -n +2 ${APP_DIR}/data/hourly_forecast.csv | sort -t, -k 24.1,24.16 -k 7 ; } > ${APP_DIR}/data/hourly_forecast_sorted.csv   

echo "Backfill finished."
