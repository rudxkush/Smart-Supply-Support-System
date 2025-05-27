#!/bin/bash

# Smart Supply Support System (4S) - Cleanup Script
# This script removes redundant files from the 4S project

echo "Cleaning up redundant files..."

# Remove redundant run scripts
rm -f run_app.sh run_break.sh run_clean.sh run_conda.sh run_direct.py run_direct.sh run_fixed.sh run_simple.sh simple_run.sh

# Remove backup/duplicate app files
rm -f app.py.bak app.py.fixed

# Keep only the essential scripts
chmod +x run.sh
chmod +x reset_db.py
chmod +x setup_venv.sh

echo "Cleanup complete. The project structure is now optimized."
echo "Use ./run.sh to start the application with various options."
echo "Run ./run.sh --help for usage information."