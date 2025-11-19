#!/usr/bin/env python3
"""
Get spawn points for a specific street/road.

Usage:
    python3 get_street_spawn_points.py <spawn_file> <street_name> [--all]
"""

import sys
import yaml
from pathlib import Path


def get_street_spawn_points(spawn_file: str, street_name: str, show_all: bool = False):
    """Get spawn points for a specific street."""
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
        print("\nAvailable streets:")
        streets = set()
        for sp in spawn_points:
            name = sp.get('road_name', 'Unnamed')
            if name:
                streets.add(name)
        for street in sorted(streets)[:20]:
            print(f"  - {street}")
        if len(streets) > 20:
            print(f"  ... and {len(streets) - 20} more")
        return 1
    
    print("="*60)
    print(f"Spawn Points on: {matching[0].get('road_name', street_name)}")
    print("="*60)
    print(f"Total spawn points: {len(matching)}")
    print("")
    
    if show_all:
        for i, sp in enumerate(matching):
            pos = sp['position']
            orient = sp.get('orientation', {})
            yaw = orient.get('yaw', 0.0)
            print(f"Spawn Point {sp['id']}:")
            print(f"  Position: ({pos['east']:.3f}, {pos['north']:.3f}, {pos['up']:.3f})")
            print(f"  Yaw: {yaw:.3f} rad ({yaw * 180 / 3.14159:.1f} deg)")
            print(f"  Gazebo Pose: {pos['east']:.6f} {pos['north']:.6f} {pos['up']:.6f} 0 0 {yaw:.6f}")
            print()
    else:
        # Show first, middle, and last
        print("First spawn point:")
        sp = matching[0]
        pos = sp['position']
        orient = sp.get('orientation', {})
        yaw = orient.get('yaw', 0.0)
        print(f"  ID: {sp['id']}")
        print(f"  Position: ({pos['east']:.3f}, {pos['north']:.3f}, {pos['up']:.3f})")
        print(f"  Yaw: {yaw:.3f} rad ({yaw * 180 / 3.14159:.1f} deg)")
        print(f"  Gazebo Pose: {pos['east']:.6f} {pos['north']:.6f} {pos['up']:.6f} 0 0 {yaw:.6f}")
        print()
        
        if len(matching) > 1:
            print("Middle spawn point:")
            sp = matching[len(matching) // 2]
            pos = sp['position']
            orient = sp.get('orientation', {})
            yaw = orient.get('yaw', 0.0)
            print(f"  ID: {sp['id']}")
            print(f"  Position: ({pos['east']:.3f}, {pos['north']:.3f}, {pos['up']:.3f})")
            print(f"  Yaw: {yaw:.3f} rad ({yaw * 180 / 3.14159:.1f} deg)")
            print(f"  Gazebo Pose: {pos['east']:.6f} {pos['north']:.6f} {pos['up']:.6f} 0 0 {yaw:.6f}")
            print()
        
        if len(matching) > 2:
            print("Last spawn point:")
            sp = matching[-1]
            pos = sp['position']
            orient = sp.get('orientation', {})
            yaw = orient.get('yaw', 0.0)
            print(f"  ID: {sp['id']}")
            print(f"  Position: ({pos['east']:.3f}, {pos['north']:.3f}, {pos['up']:.3f})")
            print(f"  Yaw: {yaw:.3f} rad ({yaw * 180 / 3.14159:.1f} deg)")
            print(f"  Gazebo Pose: {pos['east']:.6f} {pos['north']:.6f} {pos['up']:.6f} 0 0 {yaw:.6f}")
            print()
        
        print(f"Use --all to see all {len(matching)} spawn points on this street")
    
    print("="*60)
    return 0


def main():
    if len(sys.argv) < 3:
        print("Usage: get_street_spawn_points.py <spawn_file> <street_name> [--all]")
        print("\nExample:")
        print("  python3 get_street_spawn_points.py maps/bari_spawn_points.yaml 'Via Dante'")
        return 1
    
    spawn_file = sys.argv[1]
    street_name = sys.argv[2]
    show_all = '--all' in sys.argv
    
    if not Path(spawn_file).exists():
        print(f"Error: Spawn file not found: {spawn_file}")
        return 1
    
    return get_street_spawn_points(spawn_file, street_name, show_all)


if __name__ == "__main__":
    sys.exit(main())

