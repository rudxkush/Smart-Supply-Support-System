# Smart Supply Support System (4S)

A web-based application for managing supply chain operations, inventory, and support requests.

## Project Structure

```
/4S_Project/
|-- database/           # SQLite database storage
|-- static/             # Static assets (CSS, JS, images)
|-- templates/          # HTML templates
|-- app.py              # Main application file
|-- reset_db.py         # Database reset utility
|-- run.sh              # Main run script with options
|-- setup_venv.sh       # Virtual environment setup
|-- cleanup.sh          # Project cleanup utility
|-- requirements.txt    # Python dependencies
```

## Features

- Multi-role user system (Sales, Warehouse, Production, Support)
- Inventory management
- Request tracking and fulfillment
- Automated tagging and routing
- Vendor integration for support requests
- Reporting and analytics

## Setup and Running

### Quick Start

```bash
# Run the application with default settings
./run.sh
```

### Advanced Options

```bash
# Show all available options
./run.sh --help

# Run without virtual environment
./run.sh --no-venv

# Reset the database before running
./run.sh --reset-db

# Specify a custom port
./run.sh --port 5001

# Run without debug mode
./run.sh --no-debug
```

### Setup Virtual Environment Separately

```bash
# Set up a virtual environment with dependencies
./setup_venv.sh

# Activate the virtual environment
source venv/bin/activate

# Run the application
python app.py
```

The application will be accessible at http://127.0.0.1:5001
```

## Default Users

- Sales Executive: username `sales`, password `sales123`
- Warehouse Officer: username `warehouse`, password `warehouse123`
- Production Planner: username `production`, password `production123`
- Support Agent: username `support`, password `support123`

## Note for macOS Users

The application uses port 5001 instead of the default Flask port 5000 to avoid conflicts with AirPlay Receiver service on macOS.

## Project Cleanup

If you need to clean up redundant files in the project:

```bash
./cleanup.sh
```

This will remove unnecessary script files and keep only the essential ones.