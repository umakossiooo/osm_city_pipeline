# Spawning Robot Closer to Map Center

## ✅ Fixed: Robot Now Spawns Closer to Center!

The spawn script now automatically selects the spawn point **closest to the map center (0, 0)** on the requested street.

## What Changed

- **Before:** Robot spawned at first spawn point on street (could be far from center)
- **Now:** Robot spawns at spawn point **closest to center** on that street

## Closest Streets to Center

1. **Via Dante Alighieri** - Only **13.28m** from center!
   - Position: (-0.093, -13.281, 0.000)
   - Perfect for center visibility

2. **Via Marchese di Montrone** - **16.40m** from center
   - Position: (-16.384, 0.705, 0.000)
   - Also very close

## Quick Start

```bash
# Inside container
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline

# Spawn robot on Via Dante (closest to center)
python3 scripts/spawn_robot_on_street.py \
  maps/bari_spawn_points.yaml \
  "Via Dante" \
  worlds/robot_center.sdf

# Launch
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description
gz sim worlds/robot_center.sdf
```

## Pre-Created Center Spawn

**`worlds/robot_center.sdf`** - Robot on Via Dante, only 13m from center!

This is **much closer** than before:
- **Old position:** (-578, -59) = 581m from center
- **New position:** (-0.093, -13.281) = **13.28m from center** ✅

## What You'll See

- 🏙️ **3D city map** centered in view
- 🤖 **Robot on street** very close to center
- 📍 **Camera on street** looking at robot
- ✅ **Much better visibility** - everything centered!

## Spawn on Other Center Streets

```bash
# Via Marchese (also close to center)
python3 scripts/spawn_robot_on_street.py \
  maps/bari_spawn_points.yaml \
  "Marchese" \
  worlds/robot_marchese.sdf
```

The script automatically picks the spawn point closest to center on any street!

## Summary

✅ **Robot spawns closer to center** - Only 13m from (0, 0)
✅ **Better visibility** - Everything centered in view
✅ **Automatic selection** - Script picks closest spawn point
✅ **Ready to use** - `worlds/robot_center.sdf` is ready!

The robot is now much closer to the center of the map! 🎉

