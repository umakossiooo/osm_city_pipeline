# Enhanced World Generation Guide

This guide explains how to generate high-quality Gazebo worlds with detailed 3D meshes using OSM2World, while preserving road coordinates for robot navigation.

## Overview

The enhanced generation pipeline uses OSM2World to create detailed 3D meshes with:
- ✅ Realistic terrain with elevation
- ✅ Textured buildings with windows
- ✅ Vegetation (trees in parks/forests)
- ✅ Realistic road textures (asphalt, concrete)
- ✅ Proper alignment and proportions
- ✅ **Road coordinates preserved** for robot navigation and spawning

## Quick Start

### One-Command Generation

```bash
./scripts/generate_enhanced_world.sh maps/bari.osm
```

This single command:
1. Converts OSM to detailed 3D mesh using OSM2World
2. Exports road metadata (preserves coordinates)
3. Generates enhanced SDF world file

### Step-by-Step Generation

```bash
# Step 1: Convert OSM to detailed 3D mesh
./scripts/convert_with_osm2world.sh maps/bari.osm bari_3d

# Step 2: Export road metadata (preserves coordinates)
./scripts/osm-city export-metadata --osm-file maps/bari.osm

# Step 3: Generate enhanced SDF world
./scripts/osm-city generate --osm-file maps/bari.osm --enhanced
```

## Output Files

After generation, you'll have:

### World File
- `worlds/bari.sdf` - Enhanced Gazebo world with detailed 3D mesh

### Model Files
- `models/bari_3d/model.sdf` - Model definition
- `models/bari_3d/meshes/bari_3d.obj` - 3D mesh with textures
- `models/bari_3d/meshes/bari_3d.obj.mtl` - Material definitions
- `models/bari_3d/meshes/cc0textures/` - Texture library
- `models/bari_3d/meshes/custom/` - Custom textures

### Navigation Files (Road Coordinates Preserved)
- `maps/bari_roads.json` - Road coordinates for navigation
- `maps/bari_spawn_points.yaml` - Spawn points for robots

## Road Coordinate Preservation

**Critical:** Road coordinates are preserved in the metadata files, not in the mesh model. This ensures:

1. **Accurate Navigation:** Road coordinates match the original OSM data
2. **Robot Spawning:** Spawn points are correctly positioned on roads
3. **Lane Alignment:** Roads in the mesh align with coordinate data

The mesh model provides visual detail, but navigation uses the preserved coordinate data from `maps/bari_roads.json`.

## Visualization

### Setup Resource Path

```bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
```

### Launch Gazebo

```bash
# With GUI
gz sim worlds/bari.sdf

# Headless mode
gz sim --headless-rendering -s worlds/bari.sdf
```

## Configuration

Enhanced generation uses `config/enhanced.properties` which enables:
- Terrain generation
- Building colors from OSM tags
- Vegetation (trees)
- Billboards for optimized rendering
- Realistic materials and textures

## Troubleshooting

### OSM2World Not Found

If you see "OSM2World.jar not found":
1. Ensure OSM2World is available at `../map_osm_converter/osm2world/OSM2World.jar`
2. Or install OSM2World separately and set the path

### Model Not Found

If enhanced generation fails with "Model directory not found":
1. Run `./scripts/convert_with_osm2world.sh` first to generate the mesh
2. Or use `--no-enhanced` flag for basic generation

### Road Coordinates Don't Match

If road coordinates don't align with the mesh:
1. Ensure you're using the same OSM file for mesh generation and metadata export
2. Check that the ENU projection center matches between conversions
3. Road coordinates are in ENU (East-North-Up) coordinate system

## Comparison: Enhanced vs Basic

| Feature | Enhanced (OSM2World) | Basic (Simple Geometry) |
|---------|----------------------|------------------------|
| Buildings | Textured with windows | Simple boxes |
| Roads | Asphalt textures | Grey boxes |
| Terrain | Elevation data | Flat plane |
| Vegetation | Trees in parks | Green boxes |
| Textures | Realistic materials | Solid colors |
| Performance | Slower to generate | Faster to generate |
| File Size | Larger (with textures) | Smaller |

## Best Practices

1. **Always export metadata first** to preserve road coordinates
2. **Use the same OSM file** for mesh generation and metadata export
3. **Set GZ_SIM_RESOURCE_PATH** before launching Gazebo
4. **Test spawn points** using `./scripts/osm-city spawn-pose` to verify coordinates

## Integration with Navigation

The preserved road coordinates in `maps/bari_roads.json` can be used for:
- Robot spawning at specific road locations
- Path planning and navigation
- Lane-level coordinate extraction
- DRL training waypoint generation

See `maps/bari_roads.json` for the road coordinate structure.

