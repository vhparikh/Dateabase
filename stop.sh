#!/bin/bash

echo "DateABase - Shutting down application..."
echo "----------------------------------------"

# Set the ports
BACKEND_PORT=5001
FRONTEND_PORT=3000

# Function to kill processes on a specific port
kill_process_on_port() {
  local port=$1
  local service=$2
  echo "Stopping $service on port $port..."
  
  # Check if any process is using the port
  if lsof -i :$port > /dev/null; then
    echo "Found process using port $port. Terminating..."
    # Kill the process using the port
    lsof -ti :$port | xargs kill -9
    echo "$service stopped."
  else
    echo "No $service process found running on port $port."
  fi
}

# Kill processes on our ports
kill_process_on_port $BACKEND_PORT "Backend"
kill_process_on_port $FRONTEND_PORT "Frontend"

echo "----------------------------------------"
echo "Application has been shut down successfully."
echo "----------------------------------------" 