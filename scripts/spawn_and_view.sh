#!/usr/bin/env bash
# Spawn object on street and launch Gazebo to view it

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT="$SCRIPT_DIR/.."

SPAWN_FILE="${1:-maps/bari_spawn_points.yaml}"
STREET_NAME="${2:-}"
OBJECT_TYPE="${3:-box}"
OUTPUT_FILE="${4:-worlds/spawn_street.sdf}"

if [ -z "$STREET_NAME" ]; then
    echo "Usage: spawn_and_view.sh <spawn_file> <street_name> [object_type] [output_file]"
    echo ""
    echo "Example:"
    echo "  bash spawn_and_view.sh maps/bari_spawn_points.yaml 'Via Dante'"
    echo "  bash spawn_and_view.sh maps/bari_spawn_points.yaml 'Alessandro' sphere"
    exit 1
fi

cd "$PROJECT_ROOT"

echo "Creating SDF with object on street: $STREET_NAME"
python3 scripts/spawn_on_street.py "$SPAWN_FILE" "$STREET_NAME" "$OUTPUT_FILE" "$OBJECT_TYPE"

echo ""
echo "✅ SDF file created: $OUTPUT_FILE"
echo ""
echo "Launching Gazebo..."

# Source ROS setup and launch
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models

gz sim "$OUTPUT_FILE"

