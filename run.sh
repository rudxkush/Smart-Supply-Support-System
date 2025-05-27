#!/bin/bash

# Smart Supply Support System (4S) - Run Script
# This script provides a flexible way to run the 4S application

# Default settings
USE_VENV=true
RESET_DB=false
PORT=8080
DEBUG=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --no-venv)
      USE_VENV=false
      shift
      ;;
    --reset-db)
      RESET_DB=true
      shift
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --no-debug)
      DEBUG=false
      shift
      ;;
    --help)
      echo "Usage: ./run.sh [options]"
      echo "Options:"
      echo "  --no-venv     Run without virtual environment"
      echo "  --reset-db    Reset the database before running"
      echo "  --port PORT   Specify port number (default: 8080)"
      echo "  --no-debug    Disable debug mode"
      echo "  --help        Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Deactivate any active virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Deactivating current virtual environment..."
    deactivate 2>/dev/null || true
fi

# Create database directory if it doesn't exist
mkdir -p database

# Reset database if requested
if [ "$RESET_DB" = true ]; then
    echo "Initializing database..."
    python3 reset_db.py
fi

# Setup and use virtual environment if requested
if [ "$USE_VENV" = true ]; then
    echo "Setting up virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install required packages
    echo "Installing required packages..."
    pip install -q -r requirements.txt
    
    # Run the application
    echo "Starting 4S application on port $PORT..."
    if [ "$DEBUG" = true ]; then
        python app.py --port $PORT --debug
    else
        python app.py --port $PORT
    fi
    
    # Deactivate virtual environment when done
    deactivate
else
    # Run without virtual environment
    echo "Starting 4S application on port $PORT..."
    if [ "$DEBUG" = true ]; then
        python3 app.py --port $PORT --debug
    else
        python3 app.py --port $PORT
    fi
fi

echo "4S application stopped."