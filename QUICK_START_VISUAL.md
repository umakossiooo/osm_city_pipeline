# Quick Start: Visual Spawning in Gazebo

## The Problem

When you run `gz sim` directly, you get "command not found" because Gazebo needs to be sourced from ROS.

## Solution: Use the Launch Script

### Method 1: Use the All-in-One Script (Easiest!)

```bash
# Inside container
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline

# This creates the SDF AND launches Gazebo automatically
bash scripts/spawn_and_view.sh maps/bari_spawn_points.yaml "Via Dante"
```

This will:
1. ✅ Create the SDF file with object on the street
2. ✅ Source ROS setup automatically
3. ✅ Set resource path automatically
4. ✅ Launch Gazebo to show you the object!

### Method 2: Use the Launch Script

```bash
# Step 1: Create SDF (if not already created)
python3 scripts/spawn_on_street.py \
  maps/bari_spawn_points.yaml \
  "Via Dante" \
  worlds/my_spawn.sdf

# Step 2: Launch using the launch script
bash scripts/launch_gazebo.sh worlds/my_spawn.sdf
```

### Method 3: Manual Launch (If you need control)

```bash
# Step 1: Source ROS setup
source /opt/ros/jazzy/setup.bash

# Step 2: Set resource path
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models

# Step 3: Launch Gazebo
gz sim worlds/my_spawn.sdf
```

## Pre-Created Files (Ready to View!)

I've already created these files for you:

```bash
# Source ROS and set path
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models

# Launch pre-created files
gz sim worlds/spawn_via_dante.sdf        # Object on Via Dante
gz sim worlds/spawn_via_alessandro.sdf  # Object on Via Alessandro
gz sim worlds/my_spawn.sdf              # Your custom spawn
```

## Quick Reference

**Easiest way to spawn and view:**
```bash
bash scripts/spawn_and_view.sh maps/bari_spawn_points.yaml "Via Dante"
```

**View existing spawn files:**
```bash
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
gz sim worlds/spawn_via_dante.sdf
```

## What You'll See

When Gazebo launches, you'll see:
- 🏙️ The detailed 3D city map
- 🔴 A bright red box on the street
- 🟡 A yellow sphere on top (for visibility)
- 📍 Camera positioned to view the object

The object is positioned exactly on the street coordinates!

