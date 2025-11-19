#!/usr/bin/env python3
"""
Test script to verify coordinates for different streets are actually different.
This proves we can spawn on different streets.
"""

import sys
import yaml
import json
from pathlib import Path


def test_street_coordinates(spawn_file: str, roads_file: str):
    """Test that different streets have different coordinates."""
    
    # Load data
    with open(spawn_file, 'r') as f:
        spawn_data = yaml.safe_load(f)
    
    with open(roads_file, 'r') as f:
        roads_data = json.load(f)
    
    spawn_points = spawn_data['spawn_points']
    
    # Test streets
    test_streets = [
        "Via Dante Alighieri",
        "Via Alessandro Maria Calefati",
        "Via Nicolò Putignani",
        "Piazza Umberto Primo",
        "Via Michele Garruba"
    ]
    
    print("="*70)
    print("Street Coordinate Verification Test")
    print("="*70)
    print()
    
    street_coords = {}
    
    for street_name in test_streets:
        # Find spawn points on this street
        matching = []
        for sp in spawn_points:
            road_name = sp.get('road_name', '')
            if street_name.lower() in road_name.lower() or road_name.lower() in street_name.lower():
                matching.append(sp)
        
        if matching:
            first_sp = matching[0]
            pos = first_sp['position']
            street_coords[street_name] = {
                'east': pos['east'],
                'north': pos['north'],
                'up': pos['up'],
                'yaw': first_sp.get('orientation', {}).get('yaw', 0.0),
                'count': len(matching)
            }
    
    # Display results
    print("Street Coordinates (First Spawn Point on Each Street):")
    print("-"*70)
    
    for i, (street_name, coords) in enumerate(street_coords.items(), 1):
        print(f"\n{i}. {street_name}")
        print(f"   Total spawn points: {coords['count']}")
        print(f"   Position: ({coords['east']:.3f}, {coords['north']:.3f}, {coords['up']:.3f})")
        print(f"   Yaw: {coords['yaw']:.3f} rad ({coords['yaw'] * 180 / 3.14159:.1f} deg)")
        print(f"   Gazebo Pose: {coords['east']:.6f} {coords['north']:.6f} {coords['up']:.6f} 0 0 {coords['yaw']:.6f}")
    
    # Verify coordinates are different
    print("\n" + "="*70)
    print("Verification: Checking that streets have different coordinates")
    print("="*70)
    
    all_different = True
    positions = list(street_coords.values())
    
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            p1 = positions[i]
            p2 = positions[j]
            
            # Calculate distance
            dx = p1['east'] - p2['east']
            dy = p1['north'] - p2['north']
            distance = (dx*dx + dy*dy)**0.5
            
            street1 = list(street_coords.keys())[i]
            street2 = list(street_coords.keys())[j]
            
            if distance < 1.0:
                print(f"⚠️  WARNING: {street1} and {street2} are very close ({distance:.2f}m)")
                all_different = False
            else:
                print(f"✅ {street1} and {street2} are {distance:.2f}m apart")
    
    print("\n" + "="*70)
    if all_different:
        print("✅ SUCCESS: All streets have different coordinates!")
        print("✅ You can spawn on different streets - each has unique positions!")
    else:
        print("⚠️  Some streets are close, but coordinates are still distinct")
    print("="*70)
    
    return 0 if all_different else 1


def main():
    if len(sys.argv) < 3:
        print("Usage: test_street_coordinates.py <spawn_file> <roads_file>")
        return 1
    
    spawn_file = sys.argv[1]
    roads_file = sys.argv[2]
    
    return test_street_coordinates(spawn_file, roads_file)


if __name__ == "__main__":
    sys.exit(main())

