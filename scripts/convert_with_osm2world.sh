#!/usr/bin/env bash
set -euo pipefail

# Script to convert OSM to detailed 3D mesh using OSM2World
# This enhances the quality of the generated SDF world

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT="$SCRIPT_DIR/.."

INPUT_OSM=${1:-maps/bari.osm}
MODEL_NAME=${2:-city_3d}
OUTPUT_DIR="$PROJECT_ROOT/outputs/$MODEL_NAME"
MODEL_DIR="$PROJECT_ROOT/models/$MODEL_NAME"

# Resolve OSM file path
if [[ "$INPUT_OSM" = /* ]]; then
    OSM_PATH="$INPUT_OSM"
else
    OSM_PATH="$PROJECT_ROOT/$INPUT_OSM"
fi

# Check if OSM2World is available
OSM2WORLD_JAR=""
if [ -f "/opt/osm2world/OSM2World.jar" ]; then
    OSM2WORLD_JAR="/opt/osm2world/OSM2World.jar"
elif [ -f "$PROJECT_ROOT/../map_osm_converter/osm2world/OSM2World.jar" ]; then
    OSM2WORLD_JAR="$PROJECT_ROOT/../map_osm_converter/osm2world/OSM2World.jar"
else
    exit 1
fi

# Check if we're in Docker or host
IN_DOCKER=false
if [ -f /.dockerenv ] || [ -n "${DOCKER_CONTAINER:-}" ] || [ -f "/.dockerenv" ]; then
    IN_DOCKER=true
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
mkdir -p "$MODEL_DIR/meshes"

# Enhanced config path
ENHANCED_CONFIG="$PROJECT_ROOT/config/enhanced.properties"
CONFIG_ARG=""
if [ -f "$ENHANCED_CONFIG" ]; then
    CONFIG_ARG="--config $ENHANCED_CONFIG"
fi

if [ "$IN_DOCKER" = true ]; then
    java -Xms512m -Xmx4g -jar "$OSM2WORLD_JAR" \
        -i "$OSM_PATH" \
        -o "$OUTPUT_DIR/$MODEL_NAME.obj" \
        $CONFIG_ARG >/dev/null 2>&1
else
    if command -v docker &> /dev/null && docker ps | grep -q osm2world; then
        docker exec osm2world bash -c \
            "java -Xms512m -Xmx4g -jar /opt/osm2world/OSM2World.jar \
            -i /workspace/$(realpath --relative-to="$PROJECT_ROOT/.." "$OSM_PATH") \
            -o /workspace/$(realpath --relative-to="$PROJECT_ROOT/.." "$OUTPUT_DIR")/$MODEL_NAME.obj \
            $([ -f "$ENHANCED_CONFIG" ] && echo "--config /workspace/$(realpath --relative-to="$PROJECT_ROOT/.." "$ENHANCED_CONFIG")" || echo "")" >/dev/null 2>&1
    else
        java -Xms512m -Xmx4g -jar "$OSM2WORLD_JAR" \
            -i "$OSM_PATH" \
            -o "$OUTPUT_DIR/$MODEL_NAME.obj" \
            $CONFIG_ARG >/dev/null 2>&1
    fi
fi

if [ ! -f "$OUTPUT_DIR/$MODEL_NAME.obj" ]; then
    exit 1
fi

# Compute vertex normals
python3 "$SCRIPT_DIR/../tools/add_obj_normals.py" \
    "$OUTPUT_DIR/$MODEL_NAME.obj" \
    "$OUTPUT_DIR/${MODEL_NAME}_with_normals.obj" >/dev/null 2>&1 && \
    mv "$OUTPUT_DIR/${MODEL_NAME}_with_normals.obj" "$OUTPUT_DIR/$MODEL_NAME.obj"

# Copy OBJ and MTL to model directory
cp "$OUTPUT_DIR/$MODEL_NAME.obj" "$MODEL_DIR/meshes/"
[ -f "$OUTPUT_DIR/$MODEL_NAME.obj.mtl" ] && cp "$OUTPUT_DIR/$MODEL_NAME.obj.mtl" "$MODEL_DIR/meshes/" || true

# Copy textures and assets (if available)
if [ -d "$PROJECT_ROOT/../map_osm_converter/osm2world/textures" ]; then
    [ -d "$PROJECT_ROOT/../map_osm_converter/osm2world/textures/cc0textures" ] && \
        cp -r "$PROJECT_ROOT/../map_osm_converter/osm2world/textures/cc0textures" "$MODEL_DIR/meshes/" 2>/dev/null || true
    [ -d "$PROJECT_ROOT/../map_osm_converter/osm2world/textures/custom" ] && \
        cp -r "$PROJECT_ROOT/../map_osm_converter/osm2world/textures/custom" "$MODEL_DIR/meshes/" 2>/dev/null || true
    [ -d "$PROJECT_ROOT/../map_osm_converter/osm2world/models" ] && \
        cp -r "$PROJECT_ROOT/../map_osm_converter/osm2world/models" "$MODEL_DIR/meshes/" 2>/dev/null || true
    [ -d "$PROJECT_ROOT/../map_osm_converter/osm2world/resources" ] && \
        cp -r "$PROJECT_ROOT/../map_osm_converter/osm2world/resources" "$MODEL_DIR/meshes/" 2>/dev/null || true
fi

# === 5. Create model.config ===
cat <<EOF > "$MODEL_DIR/model.config"
<?xml version="1.0"?>
<model>
  <name>$MODEL_NAME</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
</model>
EOF

# === 6. Create model.sdf ===
cat <<EOF > "$MODEL_DIR/model.sdf"
<?xml version="1.0" ?>
<sdf version="1.9">
  <!-- OSM-derived city model with detailed 3D mesh from OSM2World -->
  <!-- Roads, buildings, terrain, and vegetation are all included in the mesh -->
  <model name="$MODEL_NAME">
    <static>true</static>
    <pose>0 0 0 1.5708 0 0</pose>
    <link name="${MODEL_NAME}_link">
      <!-- Road/lane visual: Uses OBJ materials/textures from OSM2World for realistic colors -->
      <!-- Visual name contains "road" and "lane" keywords for fleet_drl coordinate extractor -->
      <visual name="road_lane_street_visual">
        <geometry>
          <mesh>
            <uri>model://$MODEL_NAME/meshes/$MODEL_NAME.obj</uri>
          </mesh>
        </geometry>
        <!-- Material not specified - uses OBJ's MTL file materials for realistic textures -->
      </visual>
      <collision name="collision">
        <geometry>
          <mesh>
            <uri>model://$MODEL_NAME/meshes/$MODEL_NAME.obj</uri>
          </mesh>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
EOF


