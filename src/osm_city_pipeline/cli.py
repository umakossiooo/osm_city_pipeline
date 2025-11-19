#!/usr/bin/env python3
"""CLI for OSM City Pipeline."""

import argparse
import sys
from pathlib import Path
from typing import Optional
import json
import math
import os

# Handle both package and direct execution
try:
    from .gis_projection import project_to_enu, create_enu_from_osm, ENUProjection
    from .road_extractor import extract_road_metadata, extract_and_save_road_metadata
    from .sdf_generator import generate_sdf_world
    from .metadata_exporter import export_all_metadata, export_roads_json, export_spawn_points_yaml
    from .debug_tools import generate_debug_camera_sdf, generate_debug_spawn_sdf
    from .camera_utils import get_world_center_camera_pose, calculate_camera_pose_for_spawn_point
except ImportError:
    # If running as script, add src directory to path
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, '..', '..')
    sys.path.insert(0, os.path.abspath(src_dir))
    from osm_city_pipeline.gis_projection import project_to_enu, create_enu_from_osm, ENUProjection
    from osm_city_pipeline.road_extractor import extract_road_metadata, extract_and_save_road_metadata
    from osm_city_pipeline.sdf_generator import generate_sdf_world
    from osm_city_pipeline.metadata_exporter import export_all_metadata, export_roads_json, export_spawn_points_yaml
    from osm_city_pipeline.debug_tools import generate_debug_camera_sdf, generate_debug_spawn_sdf
    from osm_city_pipeline.camera_utils import get_world_center_camera_pose, calculate_camera_pose_for_spawn_point


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


def generate_world(args):
    """Generate Gazebo Harmonic SDF world from OSM file."""
    osm_file = args.osm_file
    output_file = args.output
    world_name = args.world_name
    
    if output_file is None:
        # Default output: worlds/<osm_file_name>.sdf
        osm_path = Path(osm_file)
        worlds_dir = Path('worlds')
        worlds_dir.mkdir(exist_ok=True)
        output_file = str(worlds_dir / f"{osm_path.stem}.sdf")
    
    try:
        print(f"Generating Gazebo world from: {osm_file}")
        print(f"Output will be saved to: {output_file}")
        print("")
        
        # Delete old file if exists (RULE 4: regenerate)
        output_path = Path(output_file)
        if output_path.exists():
            print(f"Removing old world file: {output_file}")
            output_path.unlink()
        
        # Generate SDF world
        generate_sdf_world(osm_file, output_file, world_name)
        
        print("="*60)
        print("World Generation Summary")
        print("="*60)
        print(f"World file: {output_file}")
        print(f"World name: {world_name}")
        print(f"File size: {output_path.stat().st_size} bytes")
        print("")
        print("World includes:")
        print("  - Grey drivable roads")
        print("  - Extruded buildings")
        print("  - Parks and green areas")
        print("  - Sidewalks")
        print("  - Default camera pose")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"Error during world generation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def export_metadata(args):
    """Export roads.json and spawn_points.yaml metadata."""
    osm_file = args.osm_file
    roads_output = args.roads_output
    spawn_output = args.spawn_output
    spawn_spacing = args.spawn_spacing
    
    # Default output paths
    if roads_output is None:
        osm_path = Path(osm_file)
        maps_dir = Path('maps')
        maps_dir.mkdir(exist_ok=True)
        roads_output = str(maps_dir / f"{osm_path.stem}_roads.json")
    
    if spawn_output is None:
        osm_path = Path(osm_file)
        maps_dir = Path('maps')
        maps_dir.mkdir(exist_ok=True)
        spawn_output = str(maps_dir / f"{osm_path.stem}_spawn_points.yaml")
    
    try:
        print(f"Exporting metadata from: {osm_file}")
        print(f"Roads JSON: {roads_output}")
        print(f"Spawn points YAML: {spawn_output}")
        print(f"Spawn spacing: {spawn_spacing}m")
        print("")
        
        # Delete old files if they exist (RULE 4: regenerate)
        for output_file in [roads_output, spawn_output]:
            output_path = Path(output_file)
            if output_path.exists():
                print(f"Removing old file: {output_file}")
                output_path.unlink()
        
        # Export metadata
        roads_data, spawn_points = export_all_metadata(
            osm_file, roads_output, spawn_output, spawn_spacing
        )
        
        # Display summary
        print("="*60)
        print("Metadata Export Summary")
        print("="*60)
        print(f"Roads exported: {len(roads_data['roads'])}")
        print(f"Spawn points generated: {len(spawn_points)}")
        print(f"Projection center: ({roads_data['projection_center']['latitude']:.6f}, {roads_data['projection_center']['longitude']:.6f})")
        print("")
        print(f"Files saved:")
        print(f"  - {roads_output}")
        print(f"  - {spawn_output}")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"Error during metadata export: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def debug_camera(args):
    """Generate debug SDF with camera marker."""
    osm_file = args.osm_file
    output = args.output
    
    # Default output path
    if output is None:
        osm_path = Path(osm_file)
        worlds_dir = Path('worlds')
        worlds_dir.mkdir(exist_ok=True)
        output = str(worlds_dir / "debug_camera.sdf")
    
    try:
        print(f"Generating debug camera SDF from: {osm_file}")
        print(f"Output: {output}")
        print("")
        
        # Determine camera pose
        camera_pose = None
        if args.x is not None and args.y is not None:
            # Custom position
            camera_pose = (args.x, args.y, args.z, 0.0, 1.57, 0.0)
            print(f"Using custom camera position: ({args.x}, {args.y}, {args.z})")
        else:
            # Use world center
            print("Using world center camera position")
        
        # Delete old file if exists (RULE 4)
        output_path = Path(output)
        if output_path.exists():
            print(f"Removing old file: {output}")
            output_path.unlink()
        
        # Generate debug SDF
        generate_debug_camera_sdf(osm_file, output, camera_pose)
        
        print("="*60)
        print("Debug Camera SDF Generated")
        print("="*60)
        print(f"File: {output}")
        print("")
        print("The SDF file contains:")
        print("  - Ground plane")
        print("  - Camera marker (blue box)")
        print("  - GUI camera positioned at marker")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"Error during debug camera generation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def debug_spawn(args):
    """Generate debug SDF with spawn point markers."""
    spawn_file = args.spawn_file
    output = args.output
    
    # Default output path
    if output is None:
        worlds_dir = Path('worlds')
        worlds_dir.mkdir(exist_ok=True)
        output = str(worlds_dir / "debug_spawn.sdf")
    
    try:
        print(f"Generating debug spawn SDF from: {spawn_file}")
        print(f"Output: {output}")
        print("")
        
        # Parse spawn IDs if provided
        spawn_ids = None
        if args.spawn_ids:
            spawn_ids = [int(id.strip()) for id in args.spawn_ids.split(',')]
            print(f"Visualizing spawn points: {spawn_ids}")
        else:
            print(f"Visualizing first {args.max_points} spawn points")
        
        # Delete old file if exists (RULE 4)
        output_path = Path(output)
        if output_path.exists():
            print(f"Removing old file: {output}")
            output_path.unlink()
        
        # Generate debug SDF
        generate_debug_spawn_sdf(spawn_file, output, spawn_ids, args.max_points)
        
        print("="*60)
        print("Debug Spawn SDF Generated")
        print("="*60)
        print(f"File: {output}")
        print("")
        print("The SDF file contains:")
        print("  - Ground plane")
        print("  - Spawn point markers (red spheres)")
        print("  - Direction arrows (green cylinders)")
        print("  - GUI camera positioned at first spawn point")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"Error during debug spawn generation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def reset_world(args):
    """Reset/delete generated world files and metadata."""
    osm_file = args.osm_file
    delete_all = args.all
    
    try:
        from pathlib import Path
        import os
        
        osm_path = Path(osm_file)
        base_name = osm_path.stem
        
        deleted_files = []
        
        # Delete world file
        world_file = Path('worlds') / f"{base_name}.sdf"
        if world_file.exists():
            world_file.unlink()
            deleted_files.append(str(world_file))
            print(f"Deleted: {world_file}")
        
        # Delete metadata files
        roads_file = Path('maps') / f"{base_name}_roads.json"
        if roads_file.exists():
            roads_file.unlink()
            deleted_files.append(str(roads_file))
            print(f"Deleted: {roads_file}")
        
        spawn_file = Path('maps') / f"{base_name}_spawn_points.yaml"
        if spawn_file.exists():
            spawn_file.unlink()
            deleted_files.append(str(spawn_file))
            print(f"Deleted: {spawn_file}")
        
        # Delete debug files
        debug_camera = Path('worlds') / "debug_camera.sdf"
        if debug_camera.exists():
            debug_camera.unlink()
            deleted_files.append(str(debug_camera))
            print(f"Deleted: {debug_camera}")
        
        debug_spawn = Path('worlds') / "debug_spawn.sdf"
        if debug_spawn.exists():
            debug_spawn.unlink()
            deleted_files.append(str(debug_spawn))
            print(f"Deleted: {debug_spawn}")
        
        if delete_all:
            # Delete all files in worlds/ and maps/ (except .osm files)
            worlds_dir = Path('worlds')
            if worlds_dir.exists():
                for f in worlds_dir.glob('*.sdf'):
                    if f not in deleted_files:
                        f.unlink()
                        deleted_files.append(str(f))
                        print(f"Deleted: {f}")
            
            maps_dir = Path('maps')
            if maps_dir.exists():
                for f in maps_dir.glob('*.json'):
                    if f not in deleted_files:
                        f.unlink()
                        deleted_files.append(str(f))
                        print(f"Deleted: {f}")
                for f in maps_dir.glob('*.yaml'):
                    if f not in deleted_files:
                        f.unlink()
                        deleted_files.append(str(f))
                        print(f"Deleted: {f}")
        
        print("")
        print("="*60)
        print("Reset Complete")
        print("="*60)
        print(f"Deleted {len(deleted_files)} file(s)")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"Error during reset: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def list_streets(args):
    """List all streets/roads from OSM file or roads.json."""
    try:
        import json
        
        roads_data = None
        
        if args.roads_file:
            # Load from roads.json
            with open(args.roads_file, 'r') as f:
                roads_data = json.load(f)
        elif args.osm_file:
            # Extract from OSM file
            from .metadata_exporter import export_roads_json
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                export_roads_json(args.osm_file, tmp.name)
                with open(tmp.name, 'r') as f:
                    roads_data = json.load(f)
                os.unlink(tmp.name)
        else:
            print("Error: Either --osm-file or --roads-file must be provided", file=sys.stderr)
            return 1
        
        roads = roads_data['roads']
        
        if args.named_only:
            roads = [r for r in roads if r.get('name')]
        
        print("="*60)
        print("Streets/Roads List")
        print("="*60)
        print(f"Total roads: {len(roads)}")
        if args.named_only:
            print(f"Named roads: {len(roads)}")
        print("")
        
        for i, road in enumerate(roads, 1):
            name = road.get('name', 'Unnamed')
            way_id = road.get('way_id', 'N/A')
            hw_type = road.get('highway_type', 'unknown')
            lanes = road.get('lanes', 1)
            print(f"{i:3d}. {name}")
            print(f"     Way ID: {way_id}, Type: {hw_type}, Lanes: {lanes}")
        
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"Error listing streets: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def spawn_pose(args):
    """Get spawn point pose by ID."""
    try:
        import yaml
        
        with open(args.spawn_file, 'r') as f:
            spawn_data = yaml.safe_load(f)
        
        spawn_points = spawn_data['spawn_points']
        spawn_point = next((sp for sp in spawn_points if sp['id'] == args.id), None)
        
        if spawn_point is None:
            print(f"Error: Spawn point with ID {args.id} not found", file=sys.stderr)
            return 1
        
        pos = spawn_point['position']
        orient = spawn_point.get('orientation', {})
        yaw = orient.get('yaw', 0.0)
        
        print("="*60)
        print(f"Spawn Point {args.id}")
        print("="*60)
        print(f"Name: {spawn_point.get('name', 'N/A')}")
        print(f"Position (ENU):")
        print(f"  East:  {pos['east']:.6f}")
        print(f"  North: {pos['north']:.6f}")
        print(f"  Up:    {pos['up']:.6f}")
        print(f"Orientation:")
        print(f"  Yaw:   {yaw:.6f} rad ({math.degrees(yaw):.2f} deg)")
        print(f"Road Info:")
        print(f"  Way ID: {spawn_point.get('way_id', 'N/A')}")
        print(f"  Road Name: {spawn_point.get('road_name', 'N/A')}")
        print(f"  Highway Type: {spawn_point.get('highway_type', 'N/A')}")
        print("")
        print("Gazebo Pose Format:")
        print(f"  {pos['east']:.6f} {pos['north']:.6f} {pos['up']:.6f} 0 0 {yaw:.6f}")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"Error getting spawn pose: {e}", file=sys.stderr)
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
    
    # generate-world command
    world_parser = subparsers.add_parser(
        "generate-world",
        help="Generate Gazebo Harmonic SDF world from OSM file"
    )
    world_parser.add_argument(
        "--osm-file",
        type=str,
        required=True,
        help="Path to OSM file"
    )
    world_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output SDF world file (default: worlds/<osm_file_name>.sdf)"
    )
    world_parser.add_argument(
        "--world-name",
        type=str,
        default="osm_city",
        help="Name of the world (default: osm_city)"
    )
    world_parser.set_defaults(func=generate_world)
    
    # export-metadata command
    metadata_parser = subparsers.add_parser(
        "export-metadata",
        help="Export roads.json and spawn_points.yaml metadata files"
    )
    metadata_parser.add_argument(
        "--osm-file",
        type=str,
        required=True,
        help="Path to OSM file"
    )
    metadata_parser.add_argument(
        "--roads-output",
        type=str,
        default=None,
        help="Path to output roads.json file (default: maps/<osm_file_name>_roads.json)"
    )
    metadata_parser.add_argument(
        "--spawn-output",
        type=str,
        default=None,
        help="Path to output spawn_points.yaml file (default: maps/<osm_file_name>_spawn_points.yaml)"
    )
    metadata_parser.add_argument(
        "--spawn-spacing",
        type=float,
        default=10.0,
        help="Spacing between spawn points in meters (default: 10.0)"
    )
    metadata_parser.set_defaults(func=export_metadata)
    
    # debug-camera command
    debug_camera_parser = subparsers.add_parser(
        "debug-camera",
        help="Generate debug SDF with camera marker"
    )
    debug_camera_parser.add_argument(
        "--osm-file",
        type=str,
        required=True,
        help="Path to OSM file"
    )
    debug_camera_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output SDF file (default: worlds/debug_camera.sdf)"
    )
    debug_camera_parser.add_argument(
        "--x",
        type=float,
        default=None,
        help="Camera X position (east). If not specified, uses world center."
    )
    debug_camera_parser.add_argument(
        "--y",
        type=float,
        default=None,
        help="Camera Y position (north). If not specified, uses world center."
    )
    debug_camera_parser.add_argument(
        "--z",
        type=float,
        default=50.0,
        help="Camera Z position (up, height). Default: 50.0m"
    )
    debug_camera_parser.set_defaults(func=debug_camera)
    
    # debug-spawn command
    debug_spawn_parser = subparsers.add_parser(
        "debug-spawn",
        help="Generate debug SDF with spawn point markers"
    )
    debug_spawn_parser.add_argument(
        "--spawn-file",
        type=str,
        required=True,
        help="Path to spawn_points.yaml file"
    )
    debug_spawn_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output SDF file (default: worlds/debug_spawn.sdf)"
    )
    debug_spawn_parser.add_argument(
        "--spawn-ids",
        type=str,
        default=None,
        help="Comma-separated list of spawn point IDs to visualize (e.g., '0,1,2')"
    )
    debug_spawn_parser.add_argument(
        "--max-points",
        type=int,
        default=50,
        help="Maximum number of spawn points to visualize (default: 50)"
    )
    debug_spawn_parser.set_defaults(func=debug_spawn)
    
    # generate command (alias for generate-world)
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate Gazebo world from OSM file (alias for generate-world)"
    )
    generate_parser.add_argument(
        "--osm-file",
        type=str,
        required=True,
        help="Path to OSM file"
    )
    generate_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output SDF world file (default: worlds/<osm_file_name>.sdf)"
    )
    generate_parser.add_argument(
        "--world-name",
        type=str,
        default="osm_city",
        help="Name of the world (default: osm_city)"
    )
    generate_parser.set_defaults(func=generate_world)
    
    # reset command
    reset_parser = subparsers.add_parser(
        "reset",
        help="Reset/delete generated world files and metadata"
    )
    reset_parser.add_argument(
        "--osm-file",
        type=str,
        required=True,
        help="Path to OSM file (used to determine which files to delete)"
    )
    reset_parser.add_argument(
        "--all",
        action="store_true",
        help="Delete all generated files (worlds, metadata)"
    )
    reset_parser.set_defaults(func=reset_world)
    
    # list-streets command
    list_streets_parser = subparsers.add_parser(
        "list-streets",
        help="List all streets/roads from OSM file or roads.json"
    )
    list_streets_parser.add_argument(
        "--osm-file",
        type=str,
        default=None,
        help="Path to OSM file"
    )
    list_streets_parser.add_argument(
        "--roads-file",
        type=str,
        default=None,
        help="Path to roads.json file (alternative to --osm-file)"
    )
    list_streets_parser.add_argument(
        "--named-only",
        action="store_true",
        help="Show only named streets"
    )
    list_streets_parser.set_defaults(func=list_streets)
    
    # spawn-pose command
    spawn_pose_parser = subparsers.add_parser(
        "spawn-pose",
        help="Get spawn point pose by ID"
    )
    spawn_pose_parser.add_argument(
        "--spawn-file",
        type=str,
        required=True,
        help="Path to spawn_points.yaml file"
    )
    spawn_pose_parser.add_argument(
        "--id",
        type=int,
        required=True,
        help="Spawn point ID"
    )
    spawn_pose_parser.set_defaults(func=spawn_pose)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    exit(main())
