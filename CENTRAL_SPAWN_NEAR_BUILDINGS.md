# Robot Spawn: Central Street Near Buildings

## ✅ Fixed: Robot Now Spawns in True Map Center Near Buildings!

The robot now spawns on **Via Principe Amedeo**, which is:
- **Only 14m from the TRUE map center** (not 0,0 but actual center)
- **In the city center area** where buildings are located
- **On a residential street** (perfect for urban navigation)

## What Changed

### Old Position (On Border)
- **Street:** Via Dante Alighieri
- **Position:** (-0.093, -13.281)
- **Distance from true center:** 382m ❌ (on the border!)

### New Position (True Center)
- **Street:** Via Principe Amedeo
- **Position:** (-366.9, 18.3)
- **Distance from true center:** 14m ✅ (truly central!)

## Map Center Discovery

The true map center is at **(-380.9, 18.3)**, not at (0, 0)!

- **Map bounds:** 
  - East: -1239.0 to 477.3 m
  - North: -392.9 to 429.5 m
- **True center:** (-380.9, 18.3)
- **Map size:** 1716m x 822m

## Why This Location is Better

1. ✅ **Truly central** - Only 14m from map center (vs 382m before)
2. ✅ **Near buildings** - In the city center where buildings are dense
3. ✅ **On street surface** - Z = 0.1m (on top of road)
4. ✅ **Residential street** - Good for urban navigation testing
5. ✅ **Better visibility** - Everything centered in view

## Quick Start

```bash
# Inside container
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline

# Launch (robot_center.sdf is already updated!)
source /opt/ros/jazzy/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description
gz sim worlds/robot_center.sdf
```

## Spawn Point Details

- **Street:** Via Principe Amedeo
- **Highway Type:** residential
- **Position:** (-366.9, 18.3, 0.1) m
- **Orientation:** -1.497 rad (-85.8°)
- **Distance from true center:** 14.0m

## What You'll See

- 🏙️ **3D city map** with buildings visible
- 🤖 **Robot on street** in the true center
- 📍 **Camera on street** looking at robot
- ✅ **Much better view** - everything centered, buildings nearby!

## Summary

✅ **Robot spawns in TRUE map center** - Only 14m away
✅ **Near buildings** - In city center area
✅ **On street surface** - Ready for navigation
✅ **Much better than before** - Was 382m from center, now 14m!

The robot is now in the perfect location for testing navigation in an urban environment! 🎉

