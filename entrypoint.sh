#!/bin/bash

# Ensure necessary directories exist
mkdir -p data logs output/images config

# Load crontab if it exists
if [ -f crontab ]; then
    crontab crontab
fi

MODE=$1

case "$MODE" in
    api)
        echo "Starting API..."
        exec uvicorn api:app --host 0.0.0.0 --port 8000
        ;;
    scraper)
        echo "Starting Scraper once..."
        exec python scraper.py
        ;;
    cron)
        echo "Starting Cron..."
        service cron start
        # Keep container alive by tailing a log or just staying in foreground
        tail -f /dev/null
        ;;
    all)
        echo "Starting Cron and API..."
        service cron start
        # Start API in foreground
        exec uvicorn api:app --host 0.0.0.0 --port 8000
        ;;
    *)
        echo "Usage: $0 {api|scraper|cron|all}"
        exit 1
        ;;
esac
