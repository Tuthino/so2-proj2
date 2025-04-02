#!/bin/sh
set -e

# Function to kill the running app when a USR1 signal is received.
reload_app() {
    echo "Reload signal received. Terminating app..."
    kill "$APP_PID"
}

# Trap the USR1 signal
trap reload_app USR1

while true; do
    # Start the Python app in background
    python -u client.py &
    APP_PID=$!
    
    # Wait for the Python app to finish (normally it runs until killed)
    wait "$APP_PID"
    
    echo "App terminated. Restarting..."
    # Small delay before restarting
    sleep 1
done
