#!/usr/bin/env bash
# Spawn robot on street closest to map center

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT="$SCRIPT_DIR/.."

cd "$PROJECT_ROOT"

echo "Finding street closest to map center..."

# Find closest street to center
CLOSEST=$(python3 -c "
import yaml
import math

with open('maps/bari_spawn_points.yaml', 'r') as f:
    data = yaml.safe_load(f)

closest = None
min_dist = float('inf')
for sp in data['spawn_points']:
    pos = sp['position']
    dist = math.sqrt(pos['east']**2 + pos['north']**2)
    if dist < min_dist:
        min_dist = dist
        closest = sp

road_name = closest.get('road_name', 'Unnamed')
print(road_name)
" 2>/dev/null)

if [ -z "$CLOSEST" ]; then
    echo "⚠️  Could not find closest street, using Piazza Umberto Primo"
    CLOSEST="Umberto"
fi

echo "Closest street to center: $CLOSEST"
echo ""

# Create spawn file
python3 scripts/spawn_robot_on_street.py \
  maps/bari_spawn_points.yaml \
  "$CLOSEST" \
  worlds/robot_center.sdf

echo ""
echo "✅ Robot spawn file created: worlds/robot_center.sdf"
echo "   Robot is on street closest to map center!"
echo ""
echo "To launch:"
echo "  source /opt/ros/jazzy/setup.bash"
echo "  export GZ_SIM_RESOURCE_PATH=\$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description"
echo "  gz sim worlds/robot_center.sdf"

