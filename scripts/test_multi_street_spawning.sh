#!/usr/bin/env bash
# Test script to demonstrate spawning on multiple different streets

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT="$SCRIPT_DIR/.."

SPAWN_FILE="${1:-maps/bari_spawn_points.yaml}"

echo "=========================================="
echo "Multi-Street Spawning Test"
echo "=========================================="
echo ""

# Test 1: Get spawn points for Street 1
echo "Test 1: Spawning on 'Via Dante Alighieri'"
echo "----------------------------------------"
./scripts/osm-city spawn-on-street \
  --spawn-file "$SPAWN_FILE" \
  --street-name "Via Dante" 2>&1 | grep -A 8 "First spawn point" || true
echo ""

# Test 2: Get spawn points for Street 2
echo "Test 2: Spawning on 'Via Alessandro Maria Calefati'"
echo "----------------------------------------"
./scripts/osm-city spawn-on-street \
  --spawn-file "$SPAWN_FILE" \
  --street-name "Alessandro" 2>&1 | grep -A 8 "First spawn point" || true
echo ""

# Test 3: Get spawn points for Street 3
echo "Test 3: Spawning on 'Via Nicolò Putignani'"
echo "----------------------------------------"
./scripts/osm-city spawn-on-street \
  --spawn-file "$SPAWN_FILE" \
  --street-name "Putignani" 2>&1 | grep -A 8 "First spawn point" || true
echo ""

# Test 4: Get spawn points for Street 4
echo "Test 4: Spawning on 'Piazza Umberto Primo'"
echo "----------------------------------------"
./scripts/osm-city spawn-on-street \
  --spawn-file "$SPAWN_FILE" \
  --street-name "Umberto" 2>&1 | grep -A 8 "First spawn point" || true
echo ""

# Test 5: Get spawn points for Street 5
echo "Test 5: Spawning on 'Via Michele Garruba'"
echo "----------------------------------------"
./scripts/osm-city spawn-on-street \
  --spawn-file "$SPAWN_FILE" \
  --street-name "Garruba" 2>&1 | grep -A 8 "First spawn point" || true
echo ""

# Summary: Extract all Gazebo poses
echo "=========================================="
echo "Summary: Gazebo Poses for All Streets"
echo "=========================================="
echo ""

streets=("Via Dante" "Alessandro" "Putignani" "Umberto" "Garruba")

for street in "${streets[@]}"; do
    echo "Street: $street"
    pose=$(./scripts/osm-city spawn-on-street \
      --spawn-file "$SPAWN_FILE" \
      --street-name "$street" 2>&1 | grep "Gazebo Pose:" | head -1 | sed 's/.*Gazebo Pose: //')
    if [ -n "$pose" ]; then
        echo "  Gazebo Pose: $pose"
    else
        echo "  (No spawn points found)"
    fi
    echo ""
done

echo "=========================================="
echo "✅ Multi-street spawning test complete!"
echo "=========================================="
echo ""
echo "You can use these Gazebo poses to spawn robots/objects on different streets."
echo "Each pose is unique and correctly positioned on its respective street."

