#!/bin/bash
# Start ML API with proper environment setup

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Add Node.js to PATH if not already there
if ! command -v node &> /dev/null; then
    export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
fi

# Run the API
python3 api.py

