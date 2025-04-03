#!/bin/bash
# Script to restart the 360 degree photo application
# This ensures that configuration changes are loaded properly

echo "Restarting 360 degree photo application..."

# Find and kill any running instances of the application
pkill -f "python3 run.py" || true

# Wait for processes to terminate
sleep 2

# Start the application again (adjust the path if necessary)
cd /d360/dev
nohup python3 run.py > /dev/null 2>&1 &

echo "Application restarted! Your webcam settings should now be applied."
echo "You can now take photos with your selected webcam."
