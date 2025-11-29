#!/usr/bin/env python3
"""Find central streets near buildings."""

import sys
import yaml
import math

def find_central_street_near_buildings(spawn_file, num_results=5):
    """Find streets closest to true map center."""
    with open(spawn_file, 'r') as f:
        data = yaml.safe_load(f)
    
    spawn_points = data['spawn_points']
    
    # Calculate true map center
    all_east = [sp['position']['east'] for sp in spawn_points]
    all_north = [sp['position']['north'] for sp in spawn_points]
    true_center_east = (min(all_east) + max(all_east)) / 2
    true_center_north = (min(all_north) + max(all_north)) / 2
    
    # Group spawn points by street
    streets = {}
    for sp in spawn_points:
        road_name = sp.get('road_name', 'Unnamed')
        if road_name not in streets:
            streets[road_name] = []
        streets[road_name].append(sp)
    
    # For each street, find spawn closest to true center
    street_distances = []
    for road_name, street_spawns in streets.items():
        closest_dist = float('inf')
        closest_sp = None
        for sp in street_spawns:
            pos = sp['position']
            dist = math.sqrt((pos['east'] - true_center_east)**2 + (pos['north'] - true_center_north)**2)
            if dist < closest_dist:
                closest_dist = dist
                closest_sp = sp
        street_distances.append((closest_dist, road_name, closest_sp))
    
    street_distances.sort(key=lambda x: x[0])
    
    for i, (dist, name, sp) in enumerate(street_distances[:num_results], 1):
        print(f"{name}")
    
    return street_distances[0][1] if street_distances else None

if __name__ == "__main__":
    spawn_file = sys.argv[1] if len(sys.argv) > 1 else "maps/bari_spawn_points.yaml"
    find_central_street_near_buildings(spawn_file)

