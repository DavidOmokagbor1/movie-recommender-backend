#!/bin/bash
# Startup script for Render
# This ensures the app can start even if MongoDB connection fails

echo "Starting Flask application..."
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"

# Start gunicorn
exec gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -





