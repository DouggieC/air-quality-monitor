#!/bin/bash

# Used to execute the app from cron

APP_DIR="/home/doug/apps/air-quality-monitor"
PYTHON="$APP_DIR/.venv/bin/python"
BASENAME=$(basename $0)

# Get environment variables
set -a
source ${APP_DIR}/.env
set +a

LOG_DIR="/home/doug/cron/log"
LOGFILE="${LOG_DIR}/${BASENAME}_$$.log"
LOCKFILE="/tmp/${BASENAME}.lock"

cd $APP_DIR || exit 1

# Lock to prevent overlapping runs
exec 200> $LOCKFILE
flock -n 200 || exit 1

# Execute the job
$PYTHON -m air_quality_monitor.main collect >> ${LOGFILE} 2>&1
$PYTHON -m air_quality_monitor.main predict >> ${LOGFILE} 2>&1

# Send notifications
if grep -qE "ERROR | WARNING | IQAir API" ${LOGFILE}; then
    if grep -q "ERROR" ${LOGFILE}; then
        MSG="ERROR in collection/prediction:\n$(grep -E "ERROR | WARNING | IQAir API" ${LOGFILE})"
        PRIORITY="high"
    elif grep -q "WARNING" ${LOGFILE}; then
        MSG="WARNING in collection/prediction:\n$(grep -E "WARNING | IQAir API" ${LOGFILE})"
        PRIORITY="default"
    else
        MSG="Collection/prediction completed successfully:\n$(grep -E "IQAir API" ${LOGFILE})"
        PRIORITY="low"
    fi
else
    MSG="Collection/prediction completed but no completion message found. Better check the result!"
    PRIORITY="default"
fi
    
curl -sd "${MSG}" -H "Priority: ${PRIORITY}" https://ntfy.sh/air-quality-monitor-1975
