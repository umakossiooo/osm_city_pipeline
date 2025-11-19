#!/usr/bin/env python3
"""Verify spawn point is on a street and near center."""

import sys
import yaml
import math

def verify_spawn_point(spawn_file, street_name):
    """Verify spawn point details."""
    with open(spawn_file, 'r') as f:
        data = yaml.safe_load(f)
    
    spawn_points = data['spawn_points']
    
    # Find spawn points on this street
    matching = []
    for sp in spawn_points:
        road_name = sp.get('road_name', '')
        if street_name.lower() in road_name.lower() or road_name.lower() in street_name.lower():
            matching.append(sp)
    
    if not matching:
        print(f"❌ No spawn points found for street: {street_name}")
        return False
    
    # Find closest to center
    closest = None
    min_dist = float('inf')
    for sp in matching:
        pos = sp['position']
        dist = math.sqrt(pos['east']**2 + pos['north']**2)
        if dist < min_dist:
            min_dist = dist
            closest = sp
    
    pos = closest['position']
    orient = closest.get('orientation', {})
    yaw = orient.get('yaw', 0.0)
    
    print("="*70)
    print("SPAWN POINT VERIFICATION")
    print("="*70)
    print(f"Street Name: {closest.get('road_name', 'Unknown')}")
    print(f"Highway Type: {closest.get('highway_type', 'unknown')}")
    print(f"Way ID: {closest.get('way_id', 'unknown')}")
    print(f"Spawn ID: {closest['id']}")
    print()
    print("Position (ENU coordinates):")
    print(f"  East (X):  {pos['east']:.6f} m")
    print(f"  North (Y): {pos['north']:.6f} m")
    print(f"  Up (Z):    {pos['up']:.6f} m")
    print()
    print(f"Distance from map center (0, 0): {min_dist:.2f} m")
    print(f"Orientation (yaw): {yaw:.3f} rad ({yaw * 180 / 3.14159:.1f} deg)")
    print()
    print("Robot spawn position (with 0.1m offset for wheels):")
    robot_z = pos['up'] + 0.1
    print(f"  X: {pos['east']:.6f} m")
    print(f"  Y: {pos['north']:.6f} m")
    print(f"  Z: {robot_z:.6f} m (road surface + 0.1m)")
    print()
    
    # Verify it's on a road
    highway_type = closest.get('highway_type', '')
    is_road = highway_type in ['primary', 'secondary', 'tertiary', 'residential', 
                               'unclassified', 'service', 'trunk', 'motorway']
    
    if is_road:
        print("✅ VERIFIED: Spawn point is on a road")
    else:
        print(f"⚠️  WARNING: Highway type '{highway_type}' may not be a drivable road")
    
    if min_dist < 50:
        print(f"✅ VERIFIED: Spawn point is near map center ({min_dist:.2f}m away)")
    else:
        print(f"⚠️  NOTE: Spawn point is {min_dist:.2f}m from center")
    
    print("="*70)
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: verify_spawn_point.py <spawn_file> <street_name>")
        sys.exit(1)
    
    verify_spawn_point(sys.argv[1], sys.argv[2])

