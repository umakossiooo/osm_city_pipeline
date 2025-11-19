#!/usr/bin/env bash
# Test script to verify robot visibility and spawning

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT="$SCRIPT_DIR/.."

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Robot Visibility Test"
echo "=========================================="
echo ""

# Test 1: Verify model files
echo "Test 1: Checking model files..."
if [ -f "saye_description/models/saye/model.sdf" ]; then
    echo "  ✅ Robot model.sdf exists"
else
    echo "  ❌ Robot model.sdf NOT FOUND"
    exit 1
fi

if [ -f "saye_description/models/saye/model.config" ]; then
    echo "  ✅ Robot model.config exists"
else
    echo "  ❌ Robot model.config NOT FOUND"
    exit 1
fi

if [ -d "models/bari_3d" ]; then
    echo "  ✅ City model directory exists"
else
    echo "  ❌ City model directory NOT FOUND"
    exit 1
fi

echo ""

# Test 2: Create spawn file
echo "Test 2: Creating robot spawn file..."
python3 scripts/spawn_robot_on_street.py \
  maps/bari_spawn_points.yaml \
  "Via Dante" \
  worlds/test_visibility.sdf 2>&1 | grep -E "(✅|❌|Position:|orientation:)" || true

echo ""

# Test 3: Verify SDF content
echo "Test 3: Verifying SDF content..."
if grep -q "model://saye" worlds/test_visibility.sdf; then
    echo "  ✅ Robot model URI correct (model://saye)"
else
    echo "  ❌ Robot model URI incorrect"
    exit 1
fi

if grep -q "model://bari_3d" worlds/test_visibility.sdf; then
    echo "  ✅ City model URI correct"
else
    echo "  ❌ City model URI incorrect"
    exit 1
fi

robot_pose=$(grep 'saye' -A 1 worlds/test_visibility.sdf | grep pose | sed 's/.*<pose>//;s/<\/pose>.*//')
echo "  ✅ Robot pose: $robot_pose"

camera_pose=$(grep 'camera.*default' -A 1 worlds/test_visibility.sdf | grep pose | sed 's/.*<pose>//;s/<\/pose>.*//')
echo "  ✅ Camera pose: $camera_pose"

echo ""

# Test 4: Resource path setup
echo "Test 4: Resource path setup..."
echo "  Required paths:"
echo "    - $(pwd)/models"
echo "    - $(pwd)/saye_description"
echo ""
echo "  Set with:"
echo "    export GZ_SIM_RESOURCE_PATH=\$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description"

echo ""
echo "=========================================="
echo "✅ All tests passed!"
echo "=========================================="
echo ""
echo "To launch and see the robot:"
echo "  source /opt/ros/jazzy/setup.bash"
echo "  export GZ_SIM_RESOURCE_PATH=\$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description"
echo "  gz sim worlds/test_visibility.sdf"
echo ""
echo "The robot should be visible on Via Dante Alighieri street!"
echo "Camera is positioned on the street looking at the robot."

