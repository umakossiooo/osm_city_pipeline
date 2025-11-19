# OSM City Pipeline

A pipeline for generating Gazebo Harmonic worlds from OpenStreetMap (OSM) data using ROS 2 Jazzy.

## Project Structure

```
osm_city_pipeline/
├── docker/
│   └── Dockerfile          # Docker image with ROS 2 Jazzy + Gazebo Harmonic
├── compose.yaml            # Docker Compose configuration
├── maps/                   # OSM map files (.osm)
├── worlds/                 # Generated Gazebo world files
├── src/
│   └── osm_city_pipeline/
│       ├── __init__.py
│       └── cli.py          # CLI entry point (placeholder)
├── scripts/
│   ├── generate_world.sh   # World generation script (placeholder)
│   └── reset_world.sh      # World reset script (placeholder)
└── config/
    └── pipeline_config.yaml # Pipeline configuration (placeholder)
```

## Purpose

This pipeline will convert OSM data into Gazebo Harmonic simulation worlds for robotics testing and development.

### Phase 1 (Current)
- Basic Docker environment setup
- ROS 2 Jazzy + Gazebo Harmonic installation
- Project structure initialization
- CLI placeholder

### Future Phases
- Phase 2: OSM data processing and conversion
- Phase 3: GIS library integration (pyproj, etc.)
- Phase 4: World generation from OSM data
- Phase 5: ROS 2 integration and testing

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

Or if the container is already running:

```bash
docker exec -it osm_city_pipeline bash
```

### Test the CLI Placeholder

Inside the container:

```bash
cd /workspace/osm_city_pipeline
python3 src/osm_city_pipeline/cli.py
```

### Stop the Container

```bash
docker compose down
```

## Development

The workspace is mounted at `/workspace/osm_city_pipeline` inside the container, so changes to files are immediately reflected.

## Notes

- The `worlds/` directory is persisted as a Docker volume
- The container runs with `--privileged` and `--network=host` to support Gazebo
- Display forwarding is configured for GUI applications (Gazebo)

