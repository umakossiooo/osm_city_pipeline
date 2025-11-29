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
    WORLD_NAME="${OSM_STEM}_world"
fi

# Step 0: Filter OSM to remove service roads
OSM_STEM=$(basename "$INPUT_OSM" .osm)
FILTERED_OSM="$PROJECT_ROOT/maps/${OSM_STEM}_filtered.osm"
if python3 "$SCRIPT_DIR/filter_osm.py" "$INPUT_OSM" -o "$FILTERED_OSM" >/dev/null 2>&1; then
    OSM_FOR_MESH="$FILTERED_OSM"
else
    OSM_FOR_MESH="$INPUT_OSM"
fi

# Step 1: Convert OSM to OBJ using OSM2World
MODEL_DIR="$PROJECT_ROOT/models/$MODEL_NAME"
if [ ! -d "$MODEL_DIR" ]; then
    if [ -f "$SCRIPT_DIR/convert_with_osm2world.sh" ]; then
        bash "$SCRIPT_DIR/convert_with_osm2world.sh" "$OSM_FOR_MESH" "$MODEL_NAME" >/dev/null 2>&1
    else
        exit 1
    fi
fi

# Step 2: Export road metadata
cd "$PROJECT_ROOT"
if [ -f "scripts/osm-city" ]; then
    ./scripts/osm-city export-metadata --osm-file "$INPUT_OSM" >/dev/null 2>&1 || true
fi

# Step 3: Generate enhanced SDF world
if [ -f "scripts/osm-city" ]; then
    ./scripts/osm-city generate --osm-file "$INPUT_OSM" --output "worlds/${WORLD_NAME}.sdf" --world-name "$WORLD_NAME" --enhanced >/dev/null 2>&1 || \
    ./scripts/osm-city generate --osm-file "$INPUT_OSM" --output "worlds/${WORLD_NAME}.sdf" --world-name "$WORLD_NAME" --no-enhanced >/dev/null 2>&1
else
    exit 1
fi

# Step 4: Sync outputs into the Ackermann stack (if available)
ACKERMANN_DIR=$(realpath "$PROJECT_ROOT/../ackermann-vehicle-gzsim-ros2" 2>/dev/null || true)
if [ -n "$ACKERMANN_DIR" ] && [ -d "$ACKERMANN_DIR/saye_description" ]; then
    TARGET_WORLD_DIR="$ACKERMANN_DIR/saye_description/worlds"
    mkdir -p "$TARGET_WORLD_DIR"
    cp "worlds/${WORLD_NAME}.sdf" "$TARGET_WORLD_DIR/${WORLD_NAME}.sdf" >/dev/null 2>&1

    SOURCE_MODEL_DIR="$PROJECT_ROOT/models/$MODEL_NAME"
    TARGET_MODEL_DIR="$ACKERMANN_DIR/saye_description/models/$MODEL_NAME"
    if [ -d "$SOURCE_MODEL_DIR" ]; then
        rm -rf "$TARGET_MODEL_DIR"
        mkdir -p "$TARGET_MODEL_DIR"
        cp -a "$SOURCE_MODEL_DIR/." "$TARGET_MODEL_DIR/" >/dev/null 2>&1
    fi
fi

