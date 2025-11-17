#!/bin/bash

# Start Celery Worker for File Search Indexing
# This script starts a Celery worker for processing file indexing tasks

echo "Starting Celery worker for file indexing..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Error: Redis is not running!"
    echo "Please start Redis first:"
    echo "  macOS: brew services start redis"
    echo "  Linux: sudo systemctl start redis"
    exit 1
fi

echo "Redis is running ✓"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if in correct directory
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found. Please run this script from the backend directory."
    exit 1
fi

# Determine the appropriate pool based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use threads to avoid fork issues
    POOL="threads"
    echo "Detected macOS - using threads pool"
else
    # Linux - use prefork (default)
    POOL="prefork"
    echo "Detected Linux - using prefork pool"
fi

# Start Celery worker
echo "Starting Celery worker with $POOL pool..."
echo ""

celery -A core worker \
    --loglevel=info \
    --pool=$POOL \
    --concurrency=4 \
    --max-tasks-per-child=1000

# If the worker stops
echo ""
echo "Celery worker stopped."

