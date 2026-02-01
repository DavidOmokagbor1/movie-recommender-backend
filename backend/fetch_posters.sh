#!/bin/bash
# Helper script to fetch movie posters using the correct Python version

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Use Python 3.9.6 (project's Python version)
PYTHON_BIN="/usr/bin/python3"
PYTHON_PATH="/Users/java/Library/Python/3.9/lib/python/site-packages"

# Set PYTHONPATH to include user site-packages
export PYTHONPATH="$PYTHON_PATH:$PYTHONPATH"

# Run the script with all arguments passed through
"$PYTHON_BIN" fetch_real_posters.py "$@"





