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

### 1. Generate World

```bash
./scripts/osm-city generate --osm-file maps/bari.osm
```

Output: `worlds/bari.sdf`

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
