#!/bin/bash

# Production startup script for System Logger Backend

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create log directory if it doesn't exist
mkdir -p logs

# Start with Gunicorn
echo "Starting System Logger Backend..."
gunicorn --config gunicorn_config.py sys_logger:app

