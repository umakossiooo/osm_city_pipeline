# OSM City Pipeline

Procedural city generator that converts arbitrary OpenStreetMap (OSM) extracts into segmented SDF assets ready for Gazebo Sim Harmonic and ROS 2 Jazzy workflows. The pipeline is deterministic, DRL-friendly, and enforces a single geodesy chain (WGS84 → UTM → Gazebo).

## Directory Layout

```
osm_city_pipeline/
├── generate_city.py          # Main generator
├── config/map_config.yaml    # Auto-generated coordinate metadata
├── world/city.world          # Gazebo world stub (overwritten on generation)
├── world/models/             # Per-segment assets (roads, sidewalks, buildings, vegetation)
├── spawn_points.json         # Robot spawn poses
├── camera_views.json         # Predefined DRL camera presets
└── docker/                   # Containerized runtime
```

Every run cleans and regenerates the `world/models` tree to guarantee segmentation per object class.

## Coordinate System Contract

1. **WGS84 → UTM**: All lat/lon nodes are projected via `pyproj.Transformer.from_crs("epsg:4326", f"epsg:{utm_zone}")`. The UTM zone is inferred from the dataset centroid and stored in `config/map_config.yaml`.
2. **UTM → Gazebo**: The Gazebo origin coincides with the chosen lat/lon origin. We subtract the UTM coordinates of that origin to obtain local XY (meters). A fixed yaw offset (currently `0.0`) keeps axes aligned; any future rotation would live solely inside `gazebo_offset`.
3. **Single Source of Truth**: Roads, sidewalks, buildings, vegetation, spawn points, camera views, and SDF `<pose>` blocks all consume the same transformed coordinates. Avoid hand tuning—misaligned data invalidates the pipeline.

`config/map_config.yaml` captures:

```
origin_lat: <float>
origin_lon: <float>
utm_zone: "<zone>"
gazebo_offset:
  x: <float>
  y: <float>
  yaw: <float>
```

Downstream visualization (RViz, rviz2) can re-create the transform by chaining these values.

## Running with Docker (recommended)

No host-side Python packages are required. Build and run exactly as requested:

```bash
cd /home/studente/ackermann_sim/src/osm_city_pipeline
# Build image using only the docker/ context
docker build -t osm_city_pipeline docker/

# Generate assets (example map mounted at /data)
docker run --rm -it \
  -v $(pwd):/data \
  --user $(id -u):$(id -g) \
  osm_city_pipeline \
  /data/map_osm_converter/data/bari.osm
```

The entrypoint copies `generate_city.py` from the mounted workspace into `/app/` and executes:

```
python3 /app/generate_city.py /data/... --output-dir /data

> Tip: using `--user $(id -u):$(id -g)` keeps generated files owned by your host user so cleanup is easy.
```

All artifacts (`config/`, `world/`, `spawn_points.json`, `camera_views.json`) are written directly onto the host via the bind mount.

### Environment Variables

- `OUTPUT_DIR`: optional second argument to override the output root (defaults to `/data`).

## Running with Python (optional)

If you already have Python 3.10+ with `pyproj`, `shapely`, `numpy`, `scipy`, and `PyYAML`, you can execute locally:

```bash
python3 generate_city.py path/to/map.osm --output-dir $(pwd)
```

Local installs are not required when using the Docker workflow above.

## Gazebo + ROS 2 Workflow

1. Generate the city using either Docker or local Python.
2. Launch Gazebo Harmonic:
   ```bash
   gz sim world/city.world
   ```
3. Spawn a robot with ROS 2 Jazzy:
   ```bash
   source /opt/ros/jazzy/setup.bash
   ros2 run gazebo_ros spawn_entity \
     --entity drl_agent \
     --file $(pwd)/ackermann_vehicle.urdf.xacro \
     --x $(jq -r '.[0].x' spawn_points.json) \
     --y $(jq -r '.[0].y' spawn_points.json) \
     --z $(jq -r '.[0].z' spawn_points.json) \
     --yaw $(jq -r '.[0].yaw' spawn_points.json)
   ```
4. Attach DRL camera sensors by reading `camera_views.json` and spawning sensors or static cameras at the listed poses.

## Spawn Points & Camera Views

- `spawn_points.json`: list of `{x, y, z, yaw, lane_id}` aligned with road segment centroids—ideal for initial states in DRL or scenario runners.
- `camera_views.json`: includes `long_straight`, `intersection_overhead`, `street_level_building`, and `tree_corridor` presets with `{x, y, z, yaw, pitch, roll}`.

## Asset Generation Details

- **Roads**: Highways are sliced into 50–100 m segments. Each becomes an individual SDF box with proper collision, normals, and asphalt material tones. Directory: `world/models/roads/segment_XXXXX`.
- **Sidewalks**: Derived from `sidewalk=*` metadata and explicit `footway=sidewalk` ways. Offset 1.5 m strips extruded to 12 cm height populate `world/models/sidewalks/`.
- **Buildings**: OSM footprints extruded to `height=*`, `building:levels`, or default 12 m volumes using `<polyline>` geometries in `world/models/buildings/`.
- **Trees**: `natural=tree` nodes instantiate cylinder trunks plus spherical crowns inside `world/models/vegetation/trees/`.

Each asset folder ships with `model.sdf` and `model.config` files so Gazebo can `<include>` them individually, keeping the world segmented and DRL-friendly.

## Troubleshooting

- **Missing dependencies**: Always prefer the Docker image; it already bundles ROS 2 Jazzy essentials and GIS Python wheels.
- **Misaligned geometry**: Inspect `config/map_config.yaml` and ensure downstream consumers re-use the same offset. Never apply ad-hoc offsets.
- **Empty outputs**: Confirm the OSM extract has the relevant tags (highway, building, etc.). The script skips malformed data automatically.

## Next Steps

1. Run the generator on `bari.osm` inside the container to verify outputs.
2. Integrate spawn points into your DRL reset logic.
3. Use `camera_views.json` to seed Gazebo sensors or offline dataset captures.
