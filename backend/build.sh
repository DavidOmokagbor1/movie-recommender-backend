#!/bin/bash
# Build script for Render deployment
set -e  # Exit on any error

echo "=== Upgrading pip, setuptools, and wheel ==="
python -m pip install --upgrade pip setuptools wheel

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Build completed successfully ==="

