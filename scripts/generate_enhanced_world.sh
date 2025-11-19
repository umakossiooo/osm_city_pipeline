#!/usr/bin/env bash
set -euo pipefail

# Master script to generate enhanced Gazebo world with detailed 3D mesh
# This script:
# 1. Converts OSM to detailed 3D mesh using OSM2World
# 2. Generates enhanced SDF world file
# 3. Preserves road coordinates for navigation

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT="$SCRIPT_DIR/.."

INPUT_OSM=${1:-maps/bari.osm}
MODEL_NAME=${2:-}
WORLD_NAME=${3:-}

# Determine model name from OSM file if not provided
if [ -z "$MODEL_NAME" ]; then
    OSM_STEM=$(basename "$INPUT_OSM" .osm)
    MODEL_NAME="${OSM_STEM}_3d"
fi

# Determine world name from OSM file if not provided
if [ -z "$WORLD_NAME" ]; then
    OSM_STEM=$(basename "$INPUT_OSM" .osm)
    WORLD_NAME="$OSM_STEM"
fi

echo "=========================================="
echo "Enhanced World Generation"
echo "=========================================="
echo "Input OSM: $INPUT_OSM"
echo "Model name: $MODEL_NAME"
echo "World name: $WORLD_NAME"
echo ""

# Step 1: Convert OSM to OBJ using OSM2World
echo "Step 1: Converting OSM to detailed 3D mesh..."
if [ -f "$SCRIPT_DIR/convert_with_osm2world.sh" ]; then
    bash "$SCRIPT_DIR/convert_with_osm2world.sh" "$INPUT_OSM" "$MODEL_NAME"
else
    echo "❌ convert_with_osm2world.sh not found!"
    exit 1
fi

# Step 2: Export road metadata (preserves coordinates)
echo ""
echo "Step 2: Exporting road metadata (preserves coordinates for navigation)..."
cd "$PROJECT_ROOT"
if [ -f "scripts/osm-city" ]; then
    ./scripts/osm-city export-metadata --osm-file "$INPUT_OSM" || {
        echo "⚠️  Metadata export failed, but continuing..."
    }
else
    echo "⚠️  osm-city script not found, skipping metadata export"
fi

# Step 3: Generate enhanced SDF world
echo ""
echo "Step 3: Generating enhanced SDF world..."
if [ -f "scripts/osm-city" ]; then
    ./scripts/osm-city generate --osm-file "$INPUT_OSM" --output "worlds/${WORLD_NAME}.sdf" --world-name "$WORLD_NAME" --enhanced || {
        echo "⚠️  Enhanced generation failed, trying basic generation..."
        ./scripts/osm-city generate --osm-file "$INPUT_OSM" --output "worlds/${WORLD_NAME}.sdf" --world-name "$WORLD_NAME" --no-enhanced
    }
else
    echo "❌ osm-city script not found!"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Enhanced world generation complete!"
echo "=========================================="
echo "World file: worlds/${WORLD_NAME}.sdf"
echo "Model: models/$MODEL_NAME"
echo ""
echo "Road coordinates are preserved in:"
echo "  - maps/$(basename "$INPUT_OSM" .osm)_roads.json"
echo "  - maps/$(basename "$INPUT_OSM" .osm)_spawn_points.yaml"
echo ""
echo "To visualize in Gazebo:"
echo "  export GZ_SIM_RESOURCE_PATH=\$GZ_SIM_RESOURCE_PATH:$(realpath "$PROJECT_ROOT/models")"
echo "  gz sim worlds/${WORLD_NAME}.sdf"

