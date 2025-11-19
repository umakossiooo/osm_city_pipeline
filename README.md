# OSM City Pipeline

A complete pipeline for generating Gazebo Harmonic worlds from OpenStreetMap (OSM) data using ROS 2 Jazzy.

## Project Structure

```
osm_city_pipeline/
├── docker/
│   └── Dockerfile          # Docker image with ROS 2 Jazzy + Gazebo Harmonic
├── compose.yaml            # Docker Compose configuration
├── maps/                   # OSM map files (.osm) and generated metadata
├── worlds/                 # Generated Gazebo world files (.sdf)
├── src/
│   └── osm_city_pipeline/
│       ├── __init__.py
│       ├── cli.py          # Command-line interface
│       ├── gis_projection.py    # ENU coordinate projection
│       ├── osm_parser.py        # OSM file parsing
│       ├── road_extractor.py    # Road/highway extraction
│       ├── geometry_builder.py  # 3D geometry building
│       ├── sdf_generator.py     # SDF world generation
│       ├── metadata_exporter.py # Metadata export (roads.json, spawn_points.yaml)
│       ├── camera_utils.py      # Camera positioning utilities
│       └── debug_tools.py       # Debug visualization tools
├── scripts/
│   ├── generate_world.sh   # World generation script
│   └── reset_world.sh     # World reset script
├── config/
│   └── pipeline_config.yaml # Pipeline configuration
└── tests/                  # Test suites for each phase
```

## Features

### Phase 1: Docker & Structure
- Docker environment with ROS 2 Jazzy + Gazebo Harmonic
- Project structure initialization
- CLI framework

### Phase 2: GIS Projection
- WGS84 to ENU (East-North-Up) coordinate transformation
- Automatic projection center calculation from OSM bounding box
- Deterministic coordinate conversion

### Phase 3: OSM Parsing & Road Extraction
- OSM XML/PBF file parsing
- Highway/road extraction
- Intersection detection
- Lane centerline extraction

### Phase 4: SDF World Generation
- 3D geometry building from ENU coordinates
- Gazebo Harmonic SDF world generation
- Grey drivable roads
- Extruded buildings
- Parks and green areas
- Sidewalks
- Default camera pose

### Phase 5: Metadata Export
- `roads.json`: Lane centerlines in ENU coordinates
- `spawn_points.yaml`: Spawn points on roads with orientation
- All coordinates match ENU and SDF exactly

### Phase 6: Debug Tools
- Camera visualization markers
- Spawn point visualization markers
- Debug SDF generation for verification

### Phase 7: Complete CLI
- Full command set with aliases
- Reset functionality
- Street listing
- Spawn pose queries

## Building and Running

### Prerequisites
- Docker
- Docker Compose

### Build the Docker Image

```bash
docker compose build
```

### Start the Container

```bash
docker compose up -d
```

### Enter the Container

```bash
docker compose exec osm_city_pipeline bash
```

## CLI Commands

### Generate World

Generate a Gazebo world from an OSM file:

```bash
osm-city generate --osm-file maps/bari.osm
# or
osm-city generate-world --osm-file maps/bari.osm --output worlds/bari.sdf
```

### Export Metadata

Export roads and spawn points metadata:

```bash
osm-city export-metadata --osm-file maps/bari.osm
```

### List Streets

List all streets/roads:

```bash
osm-city list-streets --roads-file maps/bari_roads.json
# or from OSM file
osm-city list-streets --osm-file maps/bari.osm --named-only
```

### Get Spawn Pose

Get spawn point pose by ID:

```bash
osm-city spawn-pose --spawn-file maps/bari_spawn_points.yaml --id 0
```

### Debug Tools

Generate debug visualization:

```bash
# Debug camera
osm-city debug-camera --osm-file maps/bari.osm

# Debug spawn points
osm-city debug-spawn --spawn-file maps/bari_spawn_points.yaml --max-points 50
```

### Reset

Delete generated files:

```bash
osm-city reset --osm-file maps/bari.osm
# or delete all
osm-city reset --osm-file maps/bari.osm --all
```

### Test Projection

Test ENU coordinate projection:

```bash
osm-city test-projection --lat 41.122 --lon 16.867 --osm-file maps/bari.osm
```

### Extract Roads

Extract road metadata:

```bash
osm-city extract-roads --osm-file maps/bari.osm --output maps/bari_metadata.json
```

## Complete Workflow

1. **Generate World:**
   ```bash
   osm-city generate --osm-file maps/bari.osm
   ```

2. **Export Metadata:**
   ```bash
   osm-city export-metadata --osm-file maps/bari.osm
   ```

3. **List Streets:**
   ```bash
   osm-city list-streets --roads-file maps/bari_roads.json
   ```

4. **Get Spawn Pose:**
   ```bash
   osm-city spawn-pose --spawn-file maps/bari_spawn_points.yaml --id 0
   ```

5. **Debug Visualization:**
   ```bash
   osm-city debug-spawn --spawn-file maps/bari_spawn_points.yaml
   ```

6. **Reset (if needed):**
   ```bash
   osm-city reset --osm-file maps/bari.osm
   ```

## Output Files

- `worlds/<name>.sdf`: Gazebo Harmonic world file
- `maps/<name>_roads.json`: Roads with ENU centerlines
- `maps/<name>_spawn_points.yaml`: Spawn points on roads
- `worlds/debug_camera.sdf`: Debug camera visualization
- `worlds/debug_spawn.sdf`: Debug spawn point visualization

## Testing

Run test suites:

```bash
# Phase 1 & 2
./tests/test_on_host.sh
./tests/test_inside_container.sh

# Phase 3
./tests/test_phase_3.sh

# Phase 4
./tests/test_phase_4.sh

# Phase 5
./tests/test_phase_5.sh
```

## Development

The workspace is mounted at `/workspace/osm_city_pipeline` inside the container, so changes to files are immediately reflected.

## Notes

- The `worlds/` directory is persisted as a Docker volume
- The container runs with `--privileged` and `--network=host` to support Gazebo
- Display forwarding is configured for GUI applications (Gazebo)
- All coordinates are in ENU (East-North-Up) system
- All outputs are deterministic (RULE 5)

## License

[Add your license here]
