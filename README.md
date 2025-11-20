# OSM City Pipeline

Convert OpenStreetMap data to detailed Gazebo Harmonic worlds with precise road coordinates for robot navigation.

## Setup

```bash
docker compose build
docker compose up -d
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline
```

## Complete Workflow

### 1. Generate Enhanced World (Recommended)

Generate a detailed 3D world with OSM2World mesh (buildings, terrain, vegetation, textures):

```bash
./scripts/generate_enhanced_world.sh maps/bari.osm
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

### 2. Spawn Robot on a Street

Spawn the robot on a specific street in the city:

```bash
# Find central streets near buildings
python3 scripts/find_central_street_near_buildings.py maps/bari_spawn_points.yaml 5

# Spawn robot on a specific street (automatically selects closest point to map center)
python3 scripts/spawn_robot_on_street.py maps/bari_spawn_points.yaml "Via Dante" worlds/robot_center.sdf
```

The script automatically:
- Finds spawn points on the requested street
- Selects the spawn point closest to the true map center (not 0,0)
- Positions the robot at correct height (0.1m above road surface)
- Configures camera on street level (2m height) looking at the robot

### 3. Visualize in Gazebo

```bash
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description

# View the world
gz sim worlds/bari.sdf

# View robot on street
gz sim worlds/robot_center.sdf

# Or use the launch script
./scripts/launch_gazebo.sh worlds/robot_center.sdf
```

## CLI Commands

The `osm-city` CLI provides additional utilities:

```bash
./scripts/osm-city <command> [options]
```

**Available Commands:**
- `generate` - Generate Gazebo world (use `--enhanced` for detailed mesh)
- `export-metadata` - Export roads and spawn points
- `list-streets` - List all streets in the map
- `spawn-pose` - Get spawn point pose by ID
- `debug-camera` - Generate debug camera visualization
- `debug-spawn` - Generate debug spawn visualization
- `reset` - Delete generated files for an OSM file
- `test-projection` - Test ENU projection
- `extract-roads` - Extract road metadata

**Examples:**

```bash
# List all streets
./scripts/osm-city list-streets --roads-file maps/bari_roads.json

# Get spawn pose by ID
./scripts/osm-city spawn-pose --spawn-file maps/bari_spawn_points.yaml --id 0

# Reset generated files
./scripts/osm-city reset --osm-file maps/bari.osm
```

## Manual Workflow (Advanced)

If you need more control, you can run steps manually:

```bash
# Step 1: Convert OSM to detailed 3D mesh
./scripts/convert_with_osm2world.sh maps/bari.osm bari_3d

# Step 2: Export road metadata (preserves coordinates)
./scripts/osm-city export-metadata --osm-file maps/bari.osm

# Step 3: Generate enhanced SDF world
./scripts/osm-city generate --osm-file maps/bari.osm --enhanced
```

## Project Structure

```
osm_city_pipeline/
├── scripts/
│   ├── generate_enhanced_world.sh    # Main workflow script
│   ├── convert_with_osm2world.sh     # OSM2World conversion
│   ├── spawn_robot_on_street.py      # Robot spawning on streets
│   ├── find_central_street_near_buildings.py  # Find central streets
│   ├── launch_gazebo.sh             # Launch Gazebo helper
│   └── osm-city                      # CLI tool
├── config/
│   └── enhanced.properties          # OSM2World configuration
├── worlds/                           # Generated SDF world files
├── models/                           # Generated 3D models
├── maps/                             # Road metadata and spawn points
└── saye_description/                 # Robot model
```

## Notes

- All commands should be run **inside the Docker container**
- Road coordinates are preserved in ENU (East-North-Up) format for accurate navigation
- The robot spawns at 0.1m above the road surface (correct height for wheels)
- Camera is positioned at street level (2m height) for realistic viewing
- The spawn point selection automatically chooses the point closest to the true map center
