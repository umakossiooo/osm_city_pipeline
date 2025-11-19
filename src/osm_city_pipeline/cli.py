#!/usr/bin/env python3
"""CLI for OSM City Pipeline."""

import argparse
import sys
from pathlib import Path
from typing import Optional
import json

# Handle both package and direct execution
try:
    from .gis_projection import project_to_enu, create_enu_from_osm, ENUProjection
    from .road_extractor import extract_road_metadata, extract_and_save_road_metadata
except ImportError:
    # If running as script, add src directory to path
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, '..', '..')
    sys.path.insert(0, os.path.abspath(src_dir))
    from osm_city_pipeline.gis_projection import project_to_enu, create_enu_from_osm, ENUProjection
    from osm_city_pipeline.road_extractor import extract_road_metadata, extract_and_save_road_metadata
    from osm_city_pipeline.road_extractor import extract_road_metadata, extract_and_save_road_metadata


def test_projection(args):
    """Test ENU projection with given coordinates."""
    lat = args.lat
    lon = args.lon
    h = args.height if args.height is not None else 0.0
    
    # Determine projection center
    center_lat = None
    center_lon = None
    osm_file_path = None
    
    if args.osm_file:
        osm_file_path = args.osm_file
        print(f"Using OSM file: {osm_file_path}")
        print("Extracting bounding box center from OSM file...")
    elif args.center_lat is not None and args.center_lon is not None:
        center_lat = args.center_lat
        center_lon = args.center_lon
        print(f"Using custom center: ({center_lat}, {center_lon})")
    else:
        # Use the point itself as center
        center_lat = lat
        center_lon = lon
        print(f"Using input point as center: ({center_lat}, {center_lon})")
    
    try:
        # Project to ENU
        if osm_file_path:
            east, north, up = project_to_enu(lat, lon, h, osm_file_path=osm_file_path)
        else:
            east, north, up = project_to_enu(lat, lon, h, 
                                            center_lat=center_lat, 
                                            center_lon=center_lon)
        
        # Display results
        print("\n" + "="*60)
        print("ENU Projection Results")
        print("="*60)
        print(f"Input WGS84:")
        print(f"  Latitude:  {lat:.8f}°")
        print(f"  Longitude: {lon:.8f}°")
        print(f"  Height:    {h:.3f} m")
        print()
        print(f"Output ENU (East-North-Up):")
        print(f"  East:  {east:.3f} m")
        print(f"  North: {north:.3f} m")
        print(f"  Up:    {up:.3f} m")
        print("="*60)
        
        # If using OSM file, show the center point
        if osm_file_path:
            enu_proj = create_enu_from_osm(osm_file_path)
            if enu_proj:
                print(f"\nProjection center (OSM bounding box center):")
                print(f"  Latitude:  {enu_proj.center_lat:.8f}°")
                print(f"  Longitude: {enu_proj.center_lon:.8f}°")
        
        return 0
    
    except Exception as e:
        print(f"Error during projection: {e}", file=sys.stderr)
        return 1


def extract_roads(args):
    """Extract roads from OSM file and save metadata."""
    osm_file = args.osm_file
    output_file = args.output
    
    if output_file is None:
        # Default output: <osm_file>_metadata.json
        osm_path = Path(osm_file)
        output_file = str(osm_path.parent / f"{osm_path.stem}_metadata.json")
    
    try:
        print(f"Extracting roads from: {osm_file}")
        print(f"Output will be saved to: {output_file}")
        print("")
        
        # Extract metadata
        metadata = extract_and_save_road_metadata(osm_file, output_file)
        
        # Display summary
        summary = metadata['summary']
        print("="*60)
        print("Road Extraction Summary")
        print("="*60)
        print(f"Total highways: {summary['total_highways']}")
        print(f"Total intersections: {summary['total_intersections']}")
        print(f"Total lane centerlines: {summary['total_lane_centerlines']}")
        print(f"Named roads: {summary['named_roads']}")
        print("")
        print("Highway types:")
        for hw_type, count in sorted(summary['highway_types'].items()):
            print(f"  {hw_type}: {count}")
        print("")
        print(f"Metadata saved to: {output_file}")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"Error during road extraction: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="OSM City Pipeline - Convert OSM data to Gazebo worlds",
        prog="osm-city"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # test-projection command
    test_parser = subparsers.add_parser(
        "test-projection",
        help="Test ENU projection with given coordinates"
    )
    test_parser.add_argument(
        "--lat",
        type=float,
        required=True,
        help="Latitude in degrees"
    )
    test_parser.add_argument(
        "--lon",
        type=float,
        required=True,
        help="Longitude in degrees"
    )
    test_parser.add_argument(
        "--height",
        type=float,
        default=None,
        help="Height in meters (default: 0.0)"
    )
    test_parser.add_argument(
        "--osm-file",
        type=str,
        default=None,
        help="Path to OSM file to use for bounding box center"
    )
    test_parser.add_argument(
        "--center-lat",
        type=float,
        default=None,
        help="Latitude of projection center (alternative to --osm-file)"
    )
    test_parser.add_argument(
        "--center-lon",
        type=float,
        default=None,
        help="Longitude of projection center (alternative to --osm-file)"
    )
    test_parser.set_defaults(func=test_projection)
    
    # extract-roads command
    extract_parser = subparsers.add_parser(
        "extract-roads",
        help="Extract roads, highways, intersections, and lane centerlines from OSM file"
    )
    extract_parser.add_argument(
        "--osm-file",
        type=str,
        required=True,
        help="Path to OSM file"
    )
    extract_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output JSON file (default: <osm_file>_metadata.json)"
    )
    extract_parser.set_defaults(func=extract_roads)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    exit(main())
