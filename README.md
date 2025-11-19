# OSM City Pipeline

Convert OpenStreetMap data to Gazebo Harmonic worlds.

## Setup

```bash
docker compose build
docker compose up -d
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline
```

## Workflow

### Option A: Enhanced Generation (Recommended)

Generate a detailed 3D world with OSM2World mesh (buildings, terrain, vegetation, textures):

```bash
# Step 1: Generate enhanced world (converts OSM to mesh + creates SDF)
./scripts/generate_enhanced_world.sh maps/bari.osm

# Or manually:
# Step 1a: Convert OSM to detailed 3D mesh
./scripts/convert_with_osm2world.sh maps/bari.osm bari_3d

# Step 1b: Generate enhanced SDF world
./scripts/osm-city generate --osm-file maps/bari.osm --enhanced
```

**Output:**
- `worlds/bari.sdf` - Enhanced world with detailed 3D mesh
- `models/bari_3d/` - Detailed 3D model with textures
- `maps/bari_roads.json` - Road coordinates (preserved for navigation)
- `maps/bari_spawn_points.yaml` - Spawn points (preserved for navigation)

**Features:**
- ✅ Detailed 3D terrain with elevation
- ✅ Textured buildings with windows
- ✅ Vegetation (trees in parks/forests)
- ✅ Realistic road textures (asphalt, concrete)
- ✅ Road coordinates preserved for robot navigation
- ✅ Proper alignment and proportions

### Option B: Basic Generation

Generate a simple world with basic geometry (faster, less detailed):

```bash
./scripts/osm-city generate --osm-file maps/bari.osm --no-enhanced
```

Output: `worlds/bari.sdf` (basic geometry: boxes for roads/buildings)

### 2. Export Metadata

```bash
./scripts/osm-city export-metadata --osm-file maps/bari.osm
```

Output: `maps/bari_roads.json`, `maps/bari_spawn_points.yaml`

### 3. List Streets

```bash
./scripts/osm-city list-streets --roads-file maps/bari_roads.json
```

### 4. Get Spawn Pose

```bash
./scripts/osm-city spawn-pose --spawn-file maps/bari_spawn_points.yaml --id 0
```

### 5. Visualize in Gazebo

```bash
source /opt/ros/jazzy/setup.bash

# Headless mode (recommended, no GUI needed):
gz sim --headless-rendering -s worlds/bari.sdf

# With GUI (requires X11 forwarding - see GAZEBO_LAUNCH.md):
gz sim worlds/bari.sdf

# Or use the launch script:
./scripts/launch_gazebo.sh worlds/bari.sdf
```

**Note:** If you see display errors, use headless mode or configure X11 forwarding (see `GAZEBO_LAUNCH.md`).

### 6. Debug Tools

```bash
# Debug camera
./scripts/osm-city debug-camera --osm-file maps/bari.osm

# Debug spawn points
./scripts/osm-city debug-spawn --spawn-file maps/bari_spawn_points.yaml
```

### 7. Reset

```bash
./scripts/osm-city reset --osm-file maps/bari.osm
```

## All Commands

```bash
./scripts/osm-city <command> [options]
```

- `generate` - Generate Gazebo world
- `export-metadata` - Export roads and spawn points
- `list-streets` - List all streets
- `spawn-pose` - Get spawn point pose by ID
- `debug-camera` - Generate debug camera visualization
- `debug-spawn` - Generate debug spawn visualization
- `reset` - Delete generated files
- `test-projection` - Test ENU projection
- `extract-roads` - Extract road metadata
