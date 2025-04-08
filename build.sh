#!/bin/bash

# Script to build the application for production deployment

echo "DateABase - Building for production..."
echo "----------------------------------------"

# Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Build completed successfully!"
echo "To deploy to Heroku, run:"
echo "git add ."
echo "git commit -m 'Build for production'"
echo "git push heroku main"
