#!/usr/bin/env bash
# Test spawning robot on multiple different streets

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT="$SCRIPT_DIR/.."

SPAWN_FILE="${1:-maps/bari_spawn_points.yaml}"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Robot Multi-Street Spawning Test"
echo "=========================================="
echo ""

# Test streets
streets=(
    "Via Dante"
    "Alessandro"
    "Putignani"
    "Umberto"
    "Garruba"
)

echo "Creating robot spawn files for ${#streets[@]} different streets..."
echo ""

for i in "${!streets[@]}"; do
    street="${streets[$i]}"
    output_file="worlds/robot_test_$((i+1)).sdf"
    
    echo "Test $((i+1)): Spawning robot on '$street'"
    python3 scripts/spawn_robot_on_street.py "$SPAWN_FILE" "$street" "$output_file" 2>&1 | grep -E "(✅|❌|Position:|orientation:)" || true
    echo ""
done

echo "=========================================="
echo "✅ Robot spawn files created!"
echo "=========================================="
echo ""
echo "Created files:"
ls -lh worlds/robot_test_*.sdf 2>/dev/null | awk '{print "  -", $9, "(" $5 ")"}'
echo ""
echo "To view a specific spawn:"
echo "  source /opt/ros/jazzy/setup.bash"
echo "  export GZ_SIM_RESOURCE_PATH=\$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description"
echo "  gz sim worlds/robot_test_1.sdf  # Via Dante"
echo "  gz sim worlds/robot_test_2.sdf  # Via Alessandro"
echo "  gz sim worlds/robot_test_3.sdf  # Via Putignani"
echo "  gz sim worlds/robot_test_4.sdf  # Piazza Umberto"
echo "  gz sim worlds/robot_test_5.sdf  # Via Garruba"
echo ""
echo "Or use the all-in-one script:"
echo "  bash scripts/spawn_robot_and_view.sh maps/bari_spawn_points.yaml 'Via Dante'"

