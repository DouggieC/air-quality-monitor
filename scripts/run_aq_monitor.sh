#!/bin/bash

# Used to execute the app from cron

APP_DIR="/home/doug/apps/air-quality-monitor"
PYTHON="$APP_DIR/.venv/bin/python"

# Get environment variables
set -a
source ${APP_DIR}/.env
set +a

LOG_DIR="/home/doug/cron/log"
LOCKFILE="/tmp/$0.lock"

cd $APP_DIR || exit 1

# Lock to prevent overlapping runs
exec 200> $LOCKFILE
flock -n 200 || exit 1

# Execute the job
$PYTHON -m air_quality_monitor.main collect >> ${LOG_DIR}/$0_$$.log 2>&1
$PYTHON -m air_quality_monitor.main predict >> ${LOG_DIR}/$0_$$.log 2>&1

# Send notifications
if grep -qE "ERROR | WARNING | IQAir API" ${LOG_DIR}/$0_$$.log; then
    if grep -q "ERROR" ${LOG_DIR}/$0_$$.log; then
        MSG="ERROR in collection/prediction:\n$(grep -E "ERROR | WARNING | IQAir API" ${LOG_DIR}/$0_$$.log)"
    elif grep -q "WARNING" ${LOG_DIR}/$0_$$.log; then
        MSG="WARNING in collection/prediction:\n$(grep -E "WARNING | IQAir API" ${LOG_DIR}/$0_$$.log)"
    else
        MSG="Collection/prediction completed successfully:\n$(grep -E "IQAir API" ${LOG_DIR}/$0_$$.log)"
    fi
else
    MSG="Collection/prediction completed but no completion message found. Better check the result!"
fi
    
curl -sd "${MSG}" https://ntfy.sh/air-quality-monitor-1975
