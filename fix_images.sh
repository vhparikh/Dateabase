#!/bin/bash

# Script to fix erroneous image URLs in the database

# Ensure we're in the project root directory
cd "$(dirname "$0")"

echo "Starting fix_image_urls.py script..."
echo "This will scan and fix problematic image URLs in the database."

# Run the Python script with python3
python3 fix_image_urls.py

echo "Script finished." 