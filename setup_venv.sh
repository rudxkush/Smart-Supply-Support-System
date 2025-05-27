#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install flask werkzeug

echo "Virtual environment setup complete. Run the following commands to activate and run the app:"
echo "source venv/bin/activate"
echo "python app.py"