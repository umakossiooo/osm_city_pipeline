#!/bin/bash
# Launch Gazebo with proper display handling

set -e

WORLD_FILE="${1:-worlds/bari.sdf}"

if [ ! -f "$WORLD_FILE" ]; then
    echo "Error: World file not found: $WORLD_FILE"
    echo "Usage: $0 [world_file]"
    exit 1
fi

echo "============================================================"
echo "Launching Gazebo with world: $WORLD_FILE"
echo "============================================================"

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash 2>/dev/null || true

# Check if DISPLAY is set and accessible
if [ -z "$DISPLAY" ]; then
    echo "Warning: DISPLAY not set. Trying headless mode..."
    gz sim --headless-rendering -s "$WORLD_FILE"
    exit 0
fi

# Try to launch with GUI
if command -v gz &> /dev/null; then
    echo "Using: gz sim"
    gz sim "$WORLD_FILE"
elif command -v gz sim &> /dev/null; then
    echo "Using: gz sim (direct)"
    gz sim "$WORLD_FILE"
elif command -v gazebo &> /dev/null; then
    echo "Using: gazebo"
    gazebo "$WORLD_FILE"
else
    echo "Error: Gazebo not found. Trying headless mode..."
    gz sim --headless-rendering -s "$WORLD_FILE"
fi
