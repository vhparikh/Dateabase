#!/bin/bash

echo "DateABase - Starting up application..."
echo "----------------------------------------"

# Set up variables
APP_ROOT="$(pwd)"
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
  kill $(lsof -t -i:$BACKEND_PORT) 2>/dev/null || true
fi

if is_port_in_use $FRONTEND_PORT; then
  echo "Killing process on port $FRONTEND_PORT"
  kill $(lsof -t -i:$FRONTEND_PORT) 2>/dev/null || true
fi

# Install backend dependencies
echo "Installing backend dependencies..."
cd "$APP_ROOT/backend"
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python -m venv venv
fi
source venv/bin/activate
pip install flask flask-cors flask-sqlalchemy PyJWT werkzeug python-dotenv gunicorn

# Reset and seed the database
echo "Resetting and seeding the database..."
if [ -f "dateabase.db" ]; then
  echo "Removing existing database..."
  rm dateabase.db
fi

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd "$APP_ROOT/frontend"
npm install --legacy-peer-deps

# Create necessary directories
if [ ! -d "public" ]; then
  mkdir -p public
fi

# Create index.html if it doesn't exist
if [ ! -f "public/index.html" ]; then
  echo "Creating index.html..."
  cat > public/index.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#000000" />
  <meta name="description" content="DateABase - Experience-based dating for Princeton" />
  <title>DateABase</title>
</head>
<body>
  <noscript>You need to enable JavaScript to run this app.</noscript>
  <div id="root"></div>
</body>
</html>
EOL
fi

# Start backend server
echo "Starting backend server on port $BACKEND_PORT..."
cd "$APP_ROOT/backend"
source venv/bin/activate
python app.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

# Start frontend server
echo "Starting frontend server on port $FRONTEND_PORT..."
cd "$APP_ROOT/frontend"
BROWSER=none npm start &
FRONTEND_PID=$!

echo "DateABase is running!"
echo "Backend: http://localhost:$BACKEND_PORT/api"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Press Ctrl+C to stop all servers"

# Handle cleanup when script exits
trap "echo 'Shutting down servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT

# Wait for processes to complete
wait 