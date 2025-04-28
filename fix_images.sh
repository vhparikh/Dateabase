#!/bin/bash

# Script to fix erroneous image URLs in the database

# Ensure we're in the project root directory
cd "$(dirname "$0")"

echo "Starting fix_image_urls.py script..."
echo "This will scan and fix problematic image URLs in the database."

# Run the Python script
python fix_image_urls.py

echo "Script finished." 