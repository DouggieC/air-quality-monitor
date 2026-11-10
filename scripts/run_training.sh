#!/bin/bash

# Runs the training job on the latest data

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

# Version is YYYYMM - monthly runs
DATE_DESC=$(date +"%b %Y")
VERSION=$(date +"%Y%m")

# Execute the job
$PYTHON -m air_quality_monitor.main prepare >> ${LOG_DIR}/$0_$$.log 2>&1 && 
    cp -p data/training_data.parquet data/training_data_${VERSION}.parquet
$PYTHON -m air_quality_monitor.main training \
    --data-version ${VERSION} \
    --data-filename data/training_data_${VERSION}.parquet \
    --data-description "Monthly run for ${DATE_DESC}" \
    >> ${LOG_DIR}/$0_$$.log 2>&1

# Send notifications
if grep -qE "ERROR | WARNING" ${LOG_DIR}/$0_$$.log; then
    if grep -q "ERROR" ${LOG_DIR}/$0_$$.log; then
        MSG="ERROR in training:\n$(grep -E "ERROR | WARNING" ${LOG_DIR}/$0_$$.log)"
        PRIORITY="high"
    elif grep -q "WARNING" ${LOG_DIR}/$0_$$.log; then
        MSG="WARNING in training:\n$(grep -E "ERROR | WARNING" ${LOG_DIR}/$0_$$.log)"
        PRIORITY="default"
    else
        MSG="Training completed successfully:\n$(grep 'Training complete:' ${LOG_DIR}/$0_$$.log)"
        PRIORITY="low"
    fi
else
    MSG="Training completed but no completion message found. Better check the result!"
    PRIORITY="default"
fi

curl -sd "${MSG}" -H "Priority: ${PRIORITY}" https://ntfy.sh/air-quality-monitor-1975

