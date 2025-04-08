#!/bin/bash

echo "Building frontend..."
cd frontend
npm install
npm run build

echo "Copying build files to backend/static..."
mkdir -p ../backend/static
cp -r build/* ../backend/static/

echo "Frontend build complete and copied to backend/static"
