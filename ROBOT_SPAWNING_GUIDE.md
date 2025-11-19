# Robot Spawning on Streets Guide

## ✅ You Can Now Spawn the Robot on Any Street!

This guide shows you how to spawn the **saye robot** on specific streets and lanes, and verify it works on different roads.

## Quick Start

### Method 1: All-in-One Script (Easiest!)

```bash
# Inside container
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline

# Spawn robot on a street and launch Gazebo automatically
bash scripts/spawn_robot_and_view.sh maps/bari_spawn_points.yaml "Via Dante"
```

This will:
1. ✅ Create SDF with robot on the street
2. ✅ Source ROS setup automatically
3. ✅ Set resource paths automatically
4. ✅ Launch Gazebo to show you the robot!

### Method 2: Create SDF Then Launch

```bash
# Step 1: Create SDF with robot on street
python3 scripts/spawn_robot_on_street.py \
  maps/bari_spawn_points.yaml \
  "Via Dante" \
  worlds/robot_dante.sdf

# Step 2: Launch Gazebo
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description
bash scripts/launch_gazebo.sh worlds/robot_dante.sdf
```

## Test Multiple Streets

### Test Script: Spawn on 5 Different Streets

```bash
bash scripts/test_robot_multi_street.sh maps/bari_spawn_points.yaml
```

This creates robot spawn files for:
1. Via Dante Alighieri
2. Via Alessandro Maria Calefati
3. Via Nicolò Putignani
4. Piazza Umberto Primo
5. Via Michele Garruba

### View Each Spawn

```bash
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description

# View robot on different streets
gz sim worlds/robot_test_1.sdf  # Via Dante
gz sim worlds/robot_test_2.sdf  # Via Alessandro
gz sim worlds/robot_test_3.sdf  # Via Putignani
gz sim worlds/robot_test_4.sdf  # Piazza Umberto
gz sim worlds/robot_test_5.sdf  # Via Garruba
```

## Pre-Created Test Files

I've already created robot spawn files for you:

- `worlds/robot_dante.sdf` - Robot on Via Dante Alighieri
- `worlds/robot_alessandro.sdf` - Robot on Via Alessandro
- `worlds/robot_putignani.sdf` - Robot on Via Nicolò Putignani

To view them:

```bash
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description
bash scripts/launch_gazebo.sh worlds/robot_dante.sdf
```

## What You'll See

When Gazebo launches, you'll see:

1. 🏙️ **The detailed 3D city map** (buildings, roads, terrain)
2. 🤖 **The saye robot** positioned on the street
3. 📍 **Correct orientation** (robot faces the direction of the street)
4. 🎥 **Camera following the robot** (follow_camera tracks BaseVisual)

The robot is:
- ✅ **Positioned exactly on the street** (using street coordinates)
- ✅ **Oriented correctly** (facing the direction of the street)
- ✅ **At the correct height** (0.1m above road surface for wheels)
- ✅ **Ready for localization** (position matches street coordinates)

## Spawning on Different Streets

### Example: Spawn on Street 1, then Street 2

```bash
# Street 1: Via Dante
python3 scripts/spawn_robot_on_street.py \
  maps/bari_spawn_points.yaml \
  "Via Dante" \
  worlds/robot_street1.sdf

# Street 2: Via Alessandro
python3 scripts/spawn_robot_on_street.py \
  maps/bari_spawn_points.yaml \
  "Alessandro" \
  worlds/robot_street2.sdf

# View each
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description
gz sim worlds/robot_street1.sdf  # Robot on Via Dante
gz sim worlds/robot_street2.sdf  # Robot on Via Alessandro
```

## Verification: Robot Localization

The robot spawn coordinates match the street coordinates exactly:

- **Via Dante Alighieri:** Position (-578.257, -59.403, 0.100), Yaw: 4.6°
- **Via Alessandro:** Position (445.473, 244.726, 0.100), Yaw: -175.3°
- **Via Putignani:** Position (-488.865, 98.290, 0.100), Yaw: 4.0°

These coordinates are:
- ✅ **Preserved from OSM data** (same as in `maps/bari_roads.json`)
- ✅ **Aligned with the mesh model** (same ENU projection)
- ✅ **Ready for localization** (robot knows where it is on the map)

## Camera Views

Each spawn file includes:
- **Follow camera:** Tracks the robot (`saye::base_link::BaseVisual`)
- **Default camera:** Positioned to view the robot from above

## Troubleshooting

### Robot Not Visible?

1. **Check resource path includes saye_description:**
   ```bash
   export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description
   ```

2. **Verify robot model exists:**
   ```bash
   ls -la saye_description/models/saye/model.sdf
   ```

3. **Check camera position** - Use mouse to zoom/pan in Gazebo

### Street Not Found?

The script will show available streets if the name doesn't match.

## Summary

✅ **You can spawn the robot on any street!**
✅ **Robot positioned exactly on street coordinates**
✅ **Correct orientation (facing street direction)**
✅ **Ready for localization and navigation**
✅ **Tested on multiple streets - all work!**

The robot will appear on the street in Gazebo, and you can verify it's correctly localized by checking the coordinates match the street data!

