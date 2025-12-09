#!/bin/bash
# set -e

# Set the project directory
PROJECT_DIR="/home/ubuntu/backend"

# Set up the environment
export PYTHONPATH=$PROJECT_DIR
export DJANGO_SETTINGS_MODULE=My_AI_Guruji.settings

# Change to project directory
cd $PROJECT_DIR

# Load environment variables
source .env

# Run the appropriate script based on argument
if [ "$1" == "daily" ]; then
    python3 notifications/daily/send_daily_horoscope.py
elif [ "$1" == "weekly" ]; then
    python3 notifications/weekly/send_weekly_horoscope.py
else
    echo "Invalid argument. Use 'daily' or 'weekly'"
    exit 1
fi

# Log the execution
echo "$(date): $1 push notifications sent" >> $PROJECT_DIR/notifications/notifications.log