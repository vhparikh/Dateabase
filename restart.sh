#!/bin/bash

echo "DateABase - Restarting application..."
echo "----------------------------------------"

# Set up variables
BACKEND_PORT=5001
FRONTEND_PORT=3000

# Function to check if a port is in use
is_port_in_use() {
  lsof -i:"$1" > /dev/null 2>&1
  return $?
}

# Kill any existing processes on the ports
echo "Cleaning up any existing processes..."
if is_port_in_use $BACKEND_PORT; then
  echo "Killing process on port $BACKEND_PORT"
  kill -9 $(lsof -t -i:$BACKEND_PORT) 2>/dev/null || true
  sleep 1
fi

if is_port_in_use $FRONTEND_PORT; then
  echo "Killing process on port $FRONTEND_PORT"
  kill -9 $(lsof -t -i:$FRONTEND_PORT) 2>/dev/null || true
  sleep 1
fi

# Verify ports are free
if is_port_in_use $BACKEND_PORT; then
  echo "ERROR: Port $BACKEND_PORT is still in use. Please free it manually."
  exit 1
fi

if is_port_in_use $FRONTEND_PORT; then
  echo "ERROR: Port $FRONTEND_PORT is still in use. Please free it manually."
  exit 1
fi

# Start backend
echo "Starting backend on port $BACKEND_PORT..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

# Check if backend started successfully
if ! is_port_in_use $BACKEND_PORT; then
  echo "ERROR: Backend failed to start. Check the logs."
  exit 1
fi

# Start frontend
echo "Starting frontend on port $FRONTEND_PORT..."
cd ../frontend
BROWSER=none npm start &
FRONTEND_PID=$!

# Wait to make sure frontend starts
sleep 3

# Check if frontend started successfully
if ! is_port_in_use $FRONTEND_PORT; then
  echo "ERROR: Frontend failed to start. Check the logs."
  kill $BACKEND_PID
  exit 1
fi

echo ""
echo "DateABase is running!"
echo "Backend: http://localhost:$BACKEND_PORT/api"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Press Ctrl+C to stop all servers"

# Handle cleanup when script exits
trap "echo 'Shutting down servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT

# Wait for processes to complete
wait 