#!/usr/bin/env python3
"""
Filter OSM file to remove unwanted highway types (service roads, driveways, etc.)
This ensures OSM2World only renders actual streets visible on the map.
"""

import xml.etree.ElementTree as ET
import argparse
import os
from pathlib import Path

# Highway types to KEEP (actual streets visible on the map)
KEEP_HIGHWAY_TYPES = {
    'motorway', 'motorway_link',
    'trunk', 'trunk_link',
    'primary', 'primary_link',
    'secondary', 'secondary_link',
    'tertiary', 'tertiary_link',
    'unclassified',
    'residential',
    # Excluded: 'service' - parking lots, driveways, internal paths
    # Excluded: 'living_street' - pedestrian-priority shared spaces
    # Excluded: 'pedestrian', 'footway', 'path', 'cycleway', etc.
}


def filter_osm(input_file: str, output_file: str) -> dict:
    """
    Filter OSM file to remove service roads and other non-street highways.
    
    Args:
        input_file: Path to input OSM file
        output_file: Path to output filtered OSM file
        
    Returns:
        Dictionary with filtering statistics
    """
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    stats = {
        'total_ways': 0,
        'removed_ways': 0,
        'kept_ways': 0,
        'removed_highway_types': {}
    }
    
    ways_to_remove = []
    
    for way in root.findall('way'):
        stats['total_ways'] += 1
        
        # Check if this way has a highway tag
        highway_tag = None
        for tag in way.findall('tag'):
            if tag.get('k') == 'highway':
                highway_tag = tag.get('v')
                break
        
        # If it's a highway type we want to remove, mark it
        if highway_tag and highway_tag not in KEEP_HIGHWAY_TYPES:
            ways_to_remove.append(way)
            stats['removed_ways'] += 1
            
            if highway_tag not in stats['removed_highway_types']:
                stats['removed_highway_types'][highway_tag] = 0
            stats['removed_highway_types'][highway_tag] += 1
        else:
            stats['kept_ways'] += 1
    
    # Remove the marked ways
    for way in ways_to_remove:
        root.remove(way)
    
    # Write filtered OSM file
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Filter OSM file to remove service roads and driveways'
    )
    parser.add_argument('input', help='Input OSM file')
    parser.add_argument('-o', '--output', help='Output filtered OSM file (default: <input>_filtered.osm)')
    
    args = parser.parse_args()
    
    input_file = args.input
    if args.output:
        output_file = args.output
    else:
        base = Path(input_file).stem
        output_file = str(Path(input_file).parent / f"{base}_filtered.osm")
    
    print(f"Filtering OSM file: {input_file}")
    print(f"Output: {output_file}")
    print()
    
    stats = filter_osm(input_file, output_file)
    
    print("=" * 50)
    print("Filtering Summary")
    print("=" * 50)
    print(f"Total ways processed: {stats['total_ways']}")
    print(f"Ways kept: {stats['kept_ways']}")
    print(f"Ways removed: {stats['removed_ways']}")
    print()
    
    if stats['removed_highway_types']:
        print("Removed highway types:")
        for hw_type, count in sorted(stats['removed_highway_types'].items()):
            print(f"  - {hw_type}: {count}")
    
    print("=" * 50)
    print(f"✅ Filtered OSM file saved: {output_file}")


if __name__ == '__main__':
    main()

