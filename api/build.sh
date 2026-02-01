#!/bin/bash
# Build script for ML API on Render
# This ensures we're in the right directory and install dependencies

set -e  # Exit on any error

echo "=== ML API Build Script ==="
echo "Current directory: $(pwd)"
echo "Listing files:"
ls -la

# Change to the API directory (in case we're in repo root)
if [ -f "requirements.txt" ]; then
    echo "Found requirements.txt in current directory"
elif [ -f "fullstack_recsys/api/requirements.txt" ]; then
    echo "Changing to fullstack_recsys/api directory"
    cd fullstack_recsys/api
elif [ -f "../api/requirements.txt" ]; then
    echo "Changing to ../api directory"
    cd ../api
fi

echo "Final directory: $(pwd)"
echo "Checking for requirements.txt:"
ls -la requirements.txt || echo "ERROR: requirements.txt not found!"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "=== Build completed successfully ==="

