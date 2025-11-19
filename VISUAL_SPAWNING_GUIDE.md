# Visual Spawning Guide - See Objects on Streets!

## ✅ You Can Now See Objects Spawning on Streets in Gazebo!

This guide shows you how to spawn **visible objects** on specific streets and see them in Gazebo.

## Quick Start

### Method 1: Use the Convenience Script

```bash
# Inside container
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline

# Spawn a red box on "Via Dante"
bash scripts/spawn_on_street.sh maps/bari_spawn_points.yaml "Via Dante"

# Then launch Gazebo to see it:
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
gz sim worlds/spawn_street.sdf
```

### Method 2: Use Python Script Directly

```bash
# Spawn on a specific street
python3 scripts/spawn_on_street.py \
  maps/bari_spawn_points.yaml \
  "Via Dante" \
  worlds/spawn_via_dante.sdf \
  box

# Launch Gazebo
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
gz sim worlds/spawn_via_dante.sdf
```

## What You'll See

When you launch the SDF file, you'll see:

1. **The detailed 3D city map** (buildings, roads, terrain)
2. **A bright red box** (1m x 0.5m x 0.3m) positioned on the street
3. **A yellow sphere** on top of the box for visibility
4. **Camera positioned** to view the spawned object

The object is:
- ✅ **Positioned exactly on the street** (using street coordinates)
- ✅ **Oriented correctly** (facing the direction of the street)
- ✅ **Visible and easy to spot** (bright red with yellow marker)
- ✅ **At the correct height** (0.5m above the road surface)

## Examples

### Example 1: Spawn on Via Dante Alighieri

```bash
python3 scripts/spawn_on_street.py \
  maps/bari_spawn_points.yaml \
  "Via Dante" \
  worlds/spawn_dante.sdf

export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
gz sim worlds/spawn_dante.sdf
```

**Result:** Red box appears on Via Dante Alighieri street!

### Example 2: Spawn on Via Alessandro

```bash
python3 scripts/spawn_on_street.py \
  maps/bari_spawn_points.yaml \
  "Alessandro" \
  worlds/spawn_alessandro.sdf

export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
gz sim worlds/spawn_alessandro.sdf
```

**Result:** Red box appears on Via Alessandro Maria Calefati street!

### Example 3: Spawn a Sphere Instead

```bash
python3 scripts/spawn_on_street.py \
  maps/bari_spawn_points.yaml \
  "Via Dante" \
  worlds/spawn_dante_sphere.sdf \
  sphere

export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
gz sim worlds/spawn_dante_sphere.sdf
```

**Result:** Bright green sphere appears on the street!

## Object Types

- **`box`** (default): Red box with yellow sphere on top (like a small car)
- **`sphere`**: Bright green glowing sphere

## Pre-Created Test Files

I've already created test files for you:

1. **`worlds/spawn_via_dante.sdf`** - Object on Via Dante Alighieri
2. **`worlds/spawn_via_alessandro.sdf`** - Object on Via Alessandro

To view them:

```bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
gz sim worlds/spawn_via_dante.sdf
# or
gz sim worlds/spawn_via_alessandro.sdf
```

## Visual Verification

When you launch Gazebo:

1. **Look for the red box** - it's positioned on the street
2. **Check the coordinates** - the object is at the exact street coordinates
3. **Verify orientation** - the box faces the direction of the street
4. **See the yellow marker** - sphere on top makes it easy to spot

## Spawning on Different Streets

To spawn on different streets, just change the street name:

```bash
# Street 1
python3 scripts/spawn_on_street.py maps/bari_spawn_points.yaml "Via Dante" worlds/street1.sdf

# Street 2  
python3 scripts/spawn_on_street.py maps/bari_spawn_points.yaml "Alessandro" worlds/street2.sdf

# Street 3
python3 scripts/spawn_on_street.py maps/bari_spawn_points.yaml "Putignani" worlds/street3.sdf
```

Each will create an SDF with the object on a different street!

## Troubleshooting

### Object Not Visible?

1. **Check resource path:**
   ```bash
   export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
   ```

2. **Verify model exists:**
   ```bash
   ls -la models/bari_3d/
   ```

3. **Check camera position** - Use mouse to zoom/pan in Gazebo

### Street Not Found?

The script will show available streets if the name doesn't match.

## Summary

✅ **You can now see objects spawning on streets visually!**
✅ **Red box appears exactly on the street coordinates**
✅ **Easy to verify spawning works correctly**
✅ **Can spawn on any street by name**
✅ **Ready-to-use SDF files created**

No more just terminal output - you can **actually see** the object on the street in Gazebo! 🎉

