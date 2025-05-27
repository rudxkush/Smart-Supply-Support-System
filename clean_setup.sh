#!/bin/bash

# Remove virtual environment
echo "Removing virtual environment..."
rm -rf venv

# Deactivate any active virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Deactivating virtual environment..."
    deactivate
fi

# Install required packages with --break-system-packages flag
echo "Installing required packages..."
pip3 install --break-system-packages flask werkzeug

# Create database directory if it doesn't exist
mkdir -p database

# Initialize database
echo "Initializing database..."
python3 reset_db.py

# Run the application with port 8080
echo "Starting 4S application on port 8080..."
python3 app.py