#!/bin/bash

# Used to execute the app from cron

APP_DIR="/home/doug/projects/air-quality-monitor"
PYTHON="$APP_DIR/.venv/bin/python"
LOG_DIR="$APP_DIR/logs"
LOCKFILE="/tmp/air_quality_monitor.lock"

cd $APP_DIR || exit 1

# Lock to prevent overlapping runs
exec 200> $LOCKFILE
flock -n 200 || exit 1

# Timestamped logfiles
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Execute the job
$PYTHON main.py >> ${LOG_DIR}/cron_run_${TIMESTAMP}.log 2>&1

