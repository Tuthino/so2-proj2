#!/bin/sh
# This script enables to restart by sendind the kill signal
# When kill signal is noticed, the app is restarted
# Without need to restart the whole container
# Example usage: docker-compose exec  server kill -USR1 <PID>
# Where <PID> is the number from the first app output


set -e

# Function to kill the running app when a USR1 signal is received.
reload_app() {
    echo "Reload signal received. Terminating app..."
    kill "$APP_PID"
}

# Trap the USR1 signal
echo "PID $$ is running run.sh with trap for USR1"
trap reload_app USR1

while true; do
    # Start the Python app in background
    python  -u server.py &
    APP_PID=$!
    
    # Wait for the Python app to finish (normally it runs until killed)
    wait "$APP_PID" || true
    
    echo "App terminated. Restarting..."
    # Small delay before restarting
    sleep 1
done
