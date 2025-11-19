#!/bin/bash
# Reset/delete generated world files and metadata

set -e

OSM_FILE="${1:-}"

if [ -z "$OSM_FILE" ]; then
    echo "Usage: $0 <osm_file> [--all]"
    echo ""
    echo "Deletes generated files for the specified OSM file:"
    echo "  - worlds/<osm_file_name>.sdf"
    echo "  - maps/<osm_file_name>_roads.json"
    echo "  - maps/<osm_file_name>_spawn_points.yaml"
    echo ""
    echo "Options:"
    echo "  --all    Delete all generated files (worlds/*.sdf, maps/*.json, maps/*.yaml)"
    exit 1
fi

# Get base name from OSM file
OSM_PATH=$(basename "$OSM_FILE")
BASE_NAME="${OSM_PATH%.osm}"
BASE_NAME="${BASE_NAME%.xml}"

DELETED=0

# Delete world file
if [ -f "worlds/${BASE_NAME}.sdf" ]; then
    rm -f "worlds/${BASE_NAME}.sdf"
    echo "Deleted: worlds/${BASE_NAME}.sdf"
    DELETED=$((DELETED + 1))
fi

# Delete metadata files
if [ -f "maps/${BASE_NAME}_roads.json" ]; then
    rm -f "maps/${BASE_NAME}_roads.json"
    echo "Deleted: maps/${BASE_NAME}_roads.json"
    DELETED=$((DELETED + 1))
fi

if [ -f "maps/${BASE_NAME}_spawn_points.yaml" ]; then
    rm -f "maps/${BASE_NAME}_spawn_points.yaml"
    echo "Deleted: maps/${BASE_NAME}_spawn_points.yaml"
    DELETED=$((DELETED + 1))
fi

# Delete debug files
if [ -f "worlds/debug_camera.sdf" ]; then
    rm -f "worlds/debug_camera.sdf"
    echo "Deleted: worlds/debug_camera.sdf"
    DELETED=$((DELETED + 1))
fi

if [ -f "worlds/debug_spawn.sdf" ]; then
    rm -f "worlds/debug_spawn.sdf"
    echo "Deleted: worlds/debug_spawn.sdf"
    DELETED=$((DELETED + 1))
fi

# Delete all if requested
if [ "$2" = "--all" ]; then
    # Delete all SDF files in worlds/
    for f in worlds/*.sdf; do
        if [ -f "$f" ]; then
            rm -f "$f"
            echo "Deleted: $f"
            DELETED=$((DELETED + 1))
        fi
    done
    
    # Delete all JSON files in maps/ (except .osm files)
    for f in maps/*.json; do
        if [ -f "$f" ]; then
            rm -f "$f"
            echo "Deleted: $f"
            DELETED=$((DELETED + 1))
        fi
    done
    
    # Delete all YAML files in maps/
    for f in maps/*.yaml; do
        if [ -f "$f" ]; then
            rm -f "$f"
            echo "Deleted: $f"
            DELETED=$((DELETED + 1))
        fi
    done
fi

echo ""
echo "============================================================"
echo "Reset Complete"
echo "============================================================"
echo "Deleted $DELETED file(s)"
echo "============================================================"
