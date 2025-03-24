#!/bin/bash

echo "DateABase - Complete Reset & Restart"
echo "----------------------------------------"

# Set up variables
BACKEND_PORT=5001
FRONTEND_PORT=3000

# Kill any existing processes on the ports
echo "Cleaning up any existing processes..."
kill -9 $(lsof -t -i:$BACKEND_PORT) 2>/dev/null || true
kill -9 $(lsof -t -i:$FRONTEND_PORT) 2>/dev/null || true
kill -9 $(pgrep -f "python app.py") 2>/dev/null || true
kill -9 $(pgrep -f "npm start") 2>/dev/null || true

# Wait to ensure processes are killed
sleep 2

# Reset database
echo "Resetting database..."
cd backend
if [ -f "dateabase.db" ]; then
  echo "Removing existing database..."
  rm dateabase.db
fi

# Make sure environment is active
source venv/bin/activate

# Install any missing packages
echo "Installing required packages..."
pip install -r requirements.txt

# Start backend
echo "Starting backend server..."
python app.py &
BACKEND_PID=$!

# Wait for backend to create and seed database
echo "Waiting for database initialization..."
sleep 5

# Start frontend
echo "Starting frontend server..."
cd ../frontend
BROWSER=none npm start &
FRONTEND_PID=$!

echo ""
echo "DateABase is running!"
echo "Backend: http://localhost:$BACKEND_PORT/api"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Press Ctrl+C to stop all servers"

# Handle cleanup when script exits
trap "echo 'Shutting down servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT

# Wait for processes to complete
wait 