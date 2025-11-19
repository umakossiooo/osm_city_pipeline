# Street-Based Spawning Guide

## ✅ Yes, You Can Spawn on Specific Streets!

You can easily:
1. **List all available streets**
2. **Get spawn points for any specific street**
3. **Spawn robots/objects on one street, then move to another**

## Quick Examples

### 1. List All Streets

```bash
# Inside container
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline

# List all streets
./scripts/osm-city list-streets --roads-file maps/bari_roads.json
```

**Output:**
- Shows all 49 streets with names, way IDs, types, and lanes
- Example: "Via Dante Alighieri", "Via Alessandro Maria Calefati", etc.

### 2. Get Spawn Points for a Specific Street

```bash
# Get spawn points on "Via Dante Alighieri"
./scripts/osm-city spawn-on-street \
  --spawn-file maps/bari_spawn_points.yaml \
  --street-name "Via Dante"
```

**Output:**
- Shows first, middle, and last spawn point on that street
- Each spawn point includes:
  - ID number
  - Position (East, North, Up coordinates)
  - Orientation (Yaw angle)
  - **Gazebo Pose Format** (ready to use!)

**Example Output:**
```
Spawn Points on: Via Dante Alighieri
Total spawn points: 137

First spawn point:
  ID: 98
  Position: (-578.257, -59.403, 0.000)
  Gazebo Pose: -578.256524 -59.403354 0.000000 0 0 0.079583
```

### 3. Get ALL Spawn Points on a Street

```bash
# See all spawn points (not just first/middle/last)
./scripts/osm-city spawn-on-street \
  --spawn-file maps/bari_spawn_points.yaml \
  --street-name "Via Dante" \
  --all
```

### 4. Spawn on Different Streets

**Example: Spawn on Street 1, then Street 2**

```bash
# Get spawn point on "Via Dante Alighieri"
./scripts/osm-city spawn-on-street \
  --spawn-file maps/bari_spawn_points.yaml \
  --street-name "Via Dante"

# Output shows: Gazebo Pose: -578.256524 -59.403354 0.000000 0 0 0.079583
# Use this pose to spawn your robot!

# Then get spawn point on "Via Alessandro"
./scripts/osm-city spawn-on-street \
  --spawn-file maps/bari_spawn_points.yaml \
  --street-name "Alessandro"

# Output shows: Gazebo Pose: 445.473142 244.726093 0.000000 0 0 -3.058752
# Use this pose to spawn on the second street!
```

## Available Streets

Your map has **49 streets** with spawn points:

- Via Alessandro Maria Calefati (139 spawn points)
- Via Nicolò Putignani (98 spawn points)
- Via Dante Alighieri (137 spawn points)
- Via Michele Garruba (75 spawn points)
- Via Beata Elia di San Clemente (15 spawn points)
- Via Marchese di Montrone (46 spawn points)
- ... and 43 more streets!

**Total: 1,397 spawn points** across all streets!

## Using Spawn Points in Gazebo

### Method 1: Use Spawn Point ID

```bash
# Get spawn point by ID (works for any street)
./scripts/osm-city spawn-pose \
  --spawn-file maps/bari_spawn_points.yaml \
  --id 98

# Output: Gazebo Pose: -578.256524 -59.403354 0.000000 0 0 0.079583
```

### Method 2: Use Street Name

```bash
# Get spawn point by street name (easier!)
./scripts/osm-city spawn-on-street \
  --spawn-file maps/bari_spawn_points.yaml \
  --street-name "Via Dante"
```

## Practical Workflow

### Scenario: Spawn Robot on Street A, Move to Street B

```bash
# Step 1: Find available streets
./scripts/osm-city list-streets --roads-file maps/bari_roads.json

# Step 2: Get spawn point on Street A (e.g., "Via Dante")
./scripts/osm-city spawn-on-street \
  --spawn-file maps/bari_spawn_points.yaml \
  --street-name "Via Dante"

# Copy the Gazebo Pose from output:
# Gazebo Pose: -578.256524 -59.403354 0.000000 0 0 0.079583

# Step 3: Spawn your robot in Gazebo using this pose
# (In your robot launch file or SDF)

# Step 4: Get spawn point on Street B (e.g., "Alessandro")
./scripts/osm-city spawn-on-street \
  --spawn-file maps/bari_spawn_points.yaml \
  --street-name "Alessandro"

# Copy the new Gazebo Pose:
# Gazebo Pose: 445.473142 244.726093 0.000000 0 0 -3.058752

# Step 5: Spawn another robot or move to this location
```

## Street Name Matching

The command supports **partial matching**, so you can use:
- Full name: `"Via Dante Alighieri"`
- Partial: `"Via Dante"` or just `"Dante"`
- Case-insensitive: `"via dante"` works too

## Finding Streets

If you're not sure of the exact name:

```bash
# List all streets to see names
./scripts/osm-city list-streets --roads-file maps/bari_roads.json

# Or try a partial name - it will show available streets if not found
./scripts/osm-city spawn-on-street \
  --spawn-file maps/bari_spawn_points.yaml \
  --street-name "nonexistent"
# Output will show available streets!
```

## Summary

✅ **You CAN spawn on specific streets!**
✅ **Easy to find streets** - use `list-streets` command
✅ **Easy to get coordinates** - use `spawn-on-street` command
✅ **Ready-to-use poses** - Gazebo Pose format included
✅ **1,397 spawn points** across 49 streets
✅ **Works for any street** - just provide the name

The system is designed exactly for this use case - spawning robots on specific streets and navigating between them!

