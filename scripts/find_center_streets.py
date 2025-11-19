#!/usr/bin/env python3
"""Find streets closest to map center."""

import sys
import yaml
import json
import math

def find_center_streets(spawn_file, roads_file, num_results=10):
    """Find streets closest to map center."""
    with open(spawn_file, 'r') as f:
        spawn_data = yaml.safe_load(f)
    
    spawn_points = spawn_data['spawn_points']
    
    # Find spawn points closest to center (0, 0, 0)
    distances = []
    for sp in spawn_points:
        pos = sp['position']
        dist = math.sqrt(pos['east']**2 + pos['north']**2)
        distances.append((dist, sp))
    
    # Sort by distance
    distances.sort(key=lambda x: x[0])
    
    print("Streets closest to map center (0, 0):")
    print("="*70)
    
    results = []
    for i, (dist, sp) in enumerate(distances[:num_results], 1):
        pos = sp['position']
        road_name = sp.get('road_name', 'Unnamed')
        results.append({
            'name': road_name,
            'distance': dist,
            'position': pos,
            'spawn_id': sp['id']
        })
        print(f"{i}. {road_name}")
        print(f"   Distance from center: {dist:.2f}m")
        print(f"   Position: ({pos['east']:.3f}, {pos['north']:.3f}, {pos['up']:.3f})")
        print(f"   Spawn ID: {sp['id']}")
        print()
    
    return results

if __name__ == "__main__":
    spawn_file = sys.argv[1] if len(sys.argv) > 1 else "maps/bari_spawn_points.yaml"
    roads_file = sys.argv[2] if len(sys.argv) > 2 else "maps/bari_roads.json"
    
    find_center_streets(spawn_file, roads_file)

