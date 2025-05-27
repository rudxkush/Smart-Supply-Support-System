#!/bin/bash

# Create a new conda environment for 4S project
echo "Creating conda environment for 4S project..."
conda create -y -n 4s_env python=3.9

# Activate conda environment
echo "Activating conda environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate 4s_env

# Install required packages
echo "Installing required packages..."
pip install flask werkzeug

# Create database directory if it doesn't exist
mkdir -p database

# Initialize database
echo "Initializing database..."
python reset_db.py

# Run the application with port 8080
echo "Starting 4S application on port 8080..."
python app.py

# Note: The environment will be deactivated when the script ends
# To use this environment later, run: conda activate 4s_env