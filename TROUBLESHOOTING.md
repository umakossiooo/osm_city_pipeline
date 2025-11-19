# Troubleshooting Guide

## Common Issues and Solutions

### Issue: Vulkan Render Engine Not Available

**Error:**
```
[Err] [RenderEngineManager.cc:496] Failed to load plugin [vulkan] : couldn't find shared library.
[Err] [RenderUtil.cc:2633] Engine [vulkan] is not supported. Loading OGRE2 instead.
```

**Solution:** ✅ **This is automatically handled!**
- Gazebo automatically falls back to OGRE2
- The spawn scripts now use OGRE2 by default (more compatible)
- This is **not an error** - OGRE2 works perfectly fine

**Status:** ✅ **Working** - Robot will spawn correctly with OGRE2

### Issue: SDF Warnings (use_parent_model_frame)

**Warning:**
```
Warning [Utils.cc:132] XML Element[use_parent_model_frame], child of element[axis], not defined in SDF.
```

**Solution:** ✅ **These are harmless warnings**
- These are SDF version compatibility warnings
- They don't affect functionality
- The robot model still loads and works correctly
- Can be safely ignored

**Status:** ✅ **Working** - Warnings don't prevent spawning

### Issue: Robot Not Visible

**Checklist:**
1. ✅ **Resource path includes saye_description:**
   ```bash
   export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description
   ```

2. ✅ **Robot model exists:**
   ```bash
   ls -la saye_description/models/saye/model.sdf
   ```

3. ✅ **Source ROS setup:**
   ```bash
   source /opt/ros/jazzy/setup.bash
   ```

4. ✅ **Check camera position** - Use mouse to zoom/pan in Gazebo

### Issue: City Model Not Visible

**Checklist:**
1. ✅ **Resource path includes models:**
   ```bash
   export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
   ```

2. ✅ **Model directory exists:**
   ```bash
   ls -la models/bari_3d/
   ```

3. ✅ **Model SDF file exists:**
   ```bash
   ls -la models/bari_3d/model.sdf
   ```

### Issue: Street Not Found

**Solution:**
- The script will show available streets if name doesn't match
- Use partial name matching (e.g., "Dante" instead of full name)
- Check available streets:
  ```bash
  ./scripts/osm-city list-streets --roads-file maps/bari_roads.json
  ```

### Issue: Gazebo Command Not Found

**Solution:**
```bash
# Always source ROS setup first
source /opt/ros/jazzy/setup.bash

# Then gz will be available
which gz
gz sim worlds/robot_dante.sdf
```

Or use the launch script:
```bash
bash scripts/launch_gazebo.sh worlds/robot_dante.sdf
```

## Render Engine Notes

- **OGRE2** (default): More compatible, works everywhere
- **Vulkan**: Faster but requires Vulkan drivers (not always available)
- Gazebo automatically falls back to OGRE2 if Vulkan unavailable

## Verification Commands

**Check if everything is set up correctly:**
```bash
# Inside container
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline

# 1. Check ROS/Gazebo
source /opt/ros/jazzy/setup.bash
which gz && echo "✅ Gazebo found"

# 2. Check models
ls -la models/bari_3d/model.sdf && echo "✅ City model found"
ls -la saye_description/models/saye/model.sdf && echo "✅ Robot model found"

# 3. Check spawn files
ls -la worlds/robot_*.sdf && echo "✅ Robot spawn files found"

# 4. Test spawn
python3 scripts/spawn_robot_on_street.py \
  maps/bari_spawn_points.yaml \
  "Via Dante" \
  worlds/test_spawn.sdf && echo "✅ Spawn script works"
```

## Summary

✅ **Vulkan warnings:** Automatically handled, OGRE2 used instead
✅ **SDF warnings:** Harmless, don't affect functionality  
✅ **Robot spawning:** Works correctly on all streets
✅ **City model:** Loads correctly
✅ **Everything is working!** 🎉

