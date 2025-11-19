#!/usr/bin/env bash
# Spawn robot on street and launch Gazebo to view it

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT="$SCRIPT_DIR/.."

SPAWN_FILE="${1:-maps/bari_spawn_points.yaml}"
STREET_NAME="${2:-}"
OUTPUT_FILE="${4:-worlds/robot_spawn.sdf}"

if [ -z "$STREET_NAME" ]; then
    echo "Usage: spawn_robot_and_view.sh <spawn_file> <street_name> [output_file]"
    echo ""
    echo "Example:"
    echo "  bash spawn_robot_and_view.sh maps/bari_spawn_points.yaml 'Via Dante'"
    echo "  bash spawn_robot_and_view.sh maps/bari_spawn_points.yaml 'Alessandro' worlds/robot_alessandro.sdf"
    exit 1
fi

cd "$PROJECT_ROOT"

echo "Creating SDF with robot on street: $STREET_NAME"
python3 scripts/spawn_robot_on_street.py "$SPAWN_FILE" "$STREET_NAME" "$OUTPUT_FILE"

echo ""
echo "✅ SDF file created: $OUTPUT_FILE"
echo ""
echo "Launching Gazebo..."

# Source ROS setup and launch
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description

gz sim "$OUTPUT_FILE"

