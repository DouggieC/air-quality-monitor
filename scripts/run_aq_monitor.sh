#!/bin/bash

# Used to execute the app from cron

APP_DIR="/home/doug/apps/air-quality-monitor"
PYTHON="$APP_DIR/.venv/bin/python"

# Get environment variables
set -a
source ${APP_DIR}/.env
set +a

LOG_DIR="/home/doug/cron/log"
LOCKFILE="/tmp/air_quality_monitor.lock"

cd $APP_DIR || exit 1

# Lock to prevent overlapping runs
exec 200> $LOCKFILE
flock -n 200 || exit 1

# Timestamped logfiles
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Execute the job
$PYTHON -m air_quality_monitor.main collect >> ${LOG_DIR}/cron_run_${$}.log 2>&1

# Send notifications
MSG=$(grep -E "ERROR | API calls" ${LOG_DIR}/cron_run_${$}.log)
curl -sd "${MSG}" https://ntfy.sh/air-quality-monitor-1975
