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

# Check if OSM2World is available (via map_osm_converter or direct)
OSM2WORLD_JAR=""
if [ -f "/opt/osm2world/OSM2World.jar" ]; then
    OSM2WORLD_JAR="/opt/osm2world/OSM2World.jar"
    echo "✅ Found OSM2World at: $OSM2WORLD_JAR"
elif [ -f "$PROJECT_ROOT/../map_osm_converter/osm2world/OSM2World.jar" ]; then
    OSM2WORLD_JAR="$PROJECT_ROOT/../map_osm_converter/osm2world/OSM2World.jar"
    echo "✅ Found OSM2World at: $OSM2WORLD_JAR"
else
    echo "❌ OSM2World.jar not found. Please ensure OSM2World is available."
    echo "   Expected locations:"
    echo "   - /opt/osm2world/OSM2World.jar (inside container)"
    echo "   - ../map_osm_converter/osm2world/OSM2World.jar (on host)"
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
    echo "✅ Using enhanced configuration"
else
    echo "⚠️  Enhanced config not found, using default OSM2World settings"
fi

# === 1. Convert OSM to OBJ with OSM2World ===
echo "🚀 Converting OSM to OBJ with OSM2World..."
echo "   Input: $OSM_PATH"
echo "   Output: $OUTPUT_DIR/$MODEL_NAME.obj"

if [ "$IN_DOCKER" = true ]; then
    # Running inside Docker
    java -Xms512m -Xmx4g -jar "$OSM2WORLD_JAR" \
        -i "$OSM_PATH" \
        -o "$OUTPUT_DIR/$MODEL_NAME.obj" \
        $CONFIG_ARG
else
    # Running on host - try to use Docker if available
    if command -v docker &> /dev/null; then
        # Check if map_osm_converter container is running
        if docker ps | grep -q osm2world; then
            echo "   Using map_osm_converter Docker container..."
            docker exec osm2world bash -c \
                "java -Xms512m -Xmx4g -jar /opt/osm2world/OSM2World.jar \
                -i /workspace/$(realpath --relative-to="$PROJECT_ROOT/.." "$OSM_PATH") \
                -o /workspace/$(realpath --relative-to="$PROJECT_ROOT/.." "$OUTPUT_DIR")/$MODEL_NAME.obj \
                $([ -f "$ENHANCED_CONFIG" ] && echo "--config /workspace/$(realpath --relative-to="$PROJECT_ROOT/.." "$ENHANCED_CONFIG")" || echo "")"
        else
            echo "   Running OSM2World directly (requires Java)..."
            java -Xms512m -Xmx4g -jar "$OSM2WORLD_JAR" \
                -i "$OSM_PATH" \
                -o "$OUTPUT_DIR/$MODEL_NAME.obj" \
                $CONFIG_ARG
        fi
    else
        echo "   Running OSM2World directly (requires Java)..."
        java -Xms512m -Xmx4g -jar "$OSM2WORLD_JAR" \
            -i "$OSM_PATH" \
            -o "$OUTPUT_DIR/$MODEL_NAME.obj" \
            $CONFIG_ARG
    fi
fi

if [ ! -f "$OUTPUT_DIR/$MODEL_NAME.obj" ]; then
    echo "❌ OSM2World conversion failed. Check logs above."
    exit 1
fi

echo "✅ OBJ file created: $OUTPUT_DIR/$MODEL_NAME.obj"

# === 2. Compute vertex normals ===
echo "🧮 Computing vertex normals..."
python3 "$SCRIPT_DIR/../tools/add_obj_normals.py" \
    "$OUTPUT_DIR/$MODEL_NAME.obj" \
    "$OUTPUT_DIR/${MODEL_NAME}_with_normals.obj" && \
    mv "$OUTPUT_DIR/${MODEL_NAME}_with_normals.obj" "$OUTPUT_DIR/$MODEL_NAME.obj"

# === 3. Copy OBJ and MTL to model directory ===
echo "📦 Packaging Gazebo model..."
cp "$OUTPUT_DIR/$MODEL_NAME.obj" "$MODEL_DIR/meshes/"
[ -f "$OUTPUT_DIR/$MODEL_NAME.obj.mtl" ] && cp "$OUTPUT_DIR/$MODEL_NAME.obj.mtl" "$MODEL_DIR/meshes/" || true

# === 4. Copy textures and assets (if available) ===
if [ -d "$PROJECT_ROOT/../map_osm_converter/osm2world/textures" ]; then
    echo "🎨 Copying OSM2World textures and assets..."
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

echo "✅ Model '$MODEL_NAME' created in $MODEL_DIR/"
echo ""
echo "To use this model, export:"
echo "  export GZ_SIM_RESOURCE_PATH=\$GZ_SIM_RESOURCE_PATH:$(realpath "$PROJECT_ROOT/models")"
echo ""
echo "Model includes:"
echo "  - Detailed 3D mesh with terrain, buildings, roads, vegetation"
echo "  - Textures and materials from OSM2World"
echo "  - Proper vertex normals for Gazebo physics"

