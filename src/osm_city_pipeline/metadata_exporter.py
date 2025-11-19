"""Export metadata files: roads.json and spawn_points.yaml."""

import json
import yaml
from typing import Dict, List, Tuple
from pathlib import Path
import math

from .gis_projection import create_enu_from_osm, ENUProjection
from .road_extractor import extract_road_metadata


def convert_centerline_to_enu(centerline: Dict, enu_proj: ENUProjection) -> List[Tuple[float, float, float]]:
    """
    Convert lane centerline from WGS84 to ENU coordinates.
    
    Args:
        centerline: Lane centerline dictionary with 'centerline' as (lat, lon) tuples
        enu_proj: ENU projection instance
    
    Returns:
        List of (east, north, up) tuples in ENU coordinates
    """
    enu_centerline = []
    
    for lat, lon in centerline['centerline']:
        e, n, u = enu_proj.project_to_enu(lat, lon, 0.0)
        enu_centerline.append((e, n, u))
    
    return enu_centerline


def export_roads_json(osm_file_path: str, output_path: str) -> Dict:
    """
    Export roads.json with lane centerlines in ENU coordinates.
    
    Args:
        osm_file_path: Path to OSM file
        output_path: Path to output JSON file
    
    Returns:
        Dictionary with exported roads data
    """
    # Create ENU projection
    enu_proj = create_enu_from_osm(osm_file_path)
    
    # Extract road metadata
    road_metadata = extract_road_metadata(osm_file_path)
    lane_centerlines = road_metadata['lane_centerlines']
    
    # Convert centerlines to ENU
    roads_data = {
        'projection_center': {
            'latitude': enu_proj.center_lat,
            'longitude': enu_proj.center_lon,
            'height': enu_proj.center_h
        },
        'roads': []
    }
    
    for centerline in lane_centerlines:
        enu_centerline = convert_centerline_to_enu(centerline, enu_proj)
        
        road_data = {
            'way_id': centerline['way_id'],
            'name': centerline['name'],
            'highway_type': centerline['highway_type'],
            'lanes': centerline['lanes'],
            'centerline_enu': [
                {'east': e, 'north': n, 'up': u}
                for e, n, u in enu_centerline
            ]
        }
        
        roads_data['roads'].append(road_data)
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(roads_data, f, indent=2, ensure_ascii=False)
    
    return roads_data


def generate_spawn_points(lane_centerlines: List[Dict], enu_proj: ENUProjection, 
                          spacing: float = 10.0) -> List[Dict]:
    """
    Generate spawn points along lane centerlines.
    Spawn points are placed exactly on centerline points or interpolated between them.
    All spawn points are guaranteed to be on the centerline.
    
    Args:
        lane_centerlines: List of lane centerline dictionaries
        enu_proj: ENU projection instance
        spacing: Spacing between spawn points in meters (default: 10.0)
    
    Returns:
        List of spawn point dictionaries with ENU coordinates
    """
    spawn_points = []
    spawn_id = 0
    
    for centerline in lane_centerlines:
        # Convert centerline to ENU
        enu_centerline = convert_centerline_to_enu(centerline, enu_proj)
        
        if len(enu_centerline) < 2:
            continue
        
        # Generate spawn points along the centerline using accumulated distance
        accumulated_distance = 0.0
        next_spawn_distance = 0.0
        
        # Always start with first point
        p1 = enu_centerline[0]
        p2 = enu_centerline[1] if len(enu_centerline) > 1 else p1
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        yaw = math.atan2(dy, dx) if (dx != 0 or dy != 0) else 0.0
        
        spawn_point = {
            'id': spawn_id,
            'name': f'spawn_point_{spawn_id}',
            'position': {
                'east': round(p1[0], 6),
                'north': round(p1[1], 6),
                'up': round(p1[2], 6)
            },
            'orientation': {
                'yaw': round(yaw, 6)
            },
            'way_id': centerline['way_id'],
            'road_name': centerline['name'],
            'highway_type': centerline['highway_type']
        }
        spawn_points.append(spawn_point)
        spawn_id += 1
        next_spawn_distance = spacing
        
        # Process segments
        for i in range(len(enu_centerline) - 1):
            p1 = enu_centerline[i]
            p2 = enu_centerline[i + 1]
            
            # Calculate segment length
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            segment_length = math.sqrt(dx*dx + dy*dy)
            
            if segment_length < 0.01:  # Skip very short segments
                accumulated_distance += segment_length
                continue
            
            segment_start_distance = accumulated_distance
            segment_end_distance = accumulated_distance + segment_length
            
            # Add spawn points at spacing intervals along this segment
            while next_spawn_distance < segment_end_distance:
                # Interpolate position along segment
                t = (next_spawn_distance - segment_start_distance) / segment_length
                e = p1[0] + t * dx
                n = p1[1] + t * dy
                u = p1[2] + t * (p2[2] - p1[2])
                yaw = math.atan2(dy, dx)
                
                spawn_point = {
                    'id': spawn_id,
                    'name': f'spawn_point_{spawn_id}',
                    'position': {
                        'east': round(e, 6),
                        'north': round(n, 6),
                        'up': round(u, 6)
                    },
                    'orientation': {
                        'yaw': round(yaw, 6)
                    },
                    'way_id': centerline['way_id'],
                    'road_name': centerline['name'],
                    'highway_type': centerline['highway_type']
                }
                
                spawn_points.append(spawn_point)
                spawn_id += 1
                next_spawn_distance += spacing
            
            accumulated_distance = segment_end_distance
        
        # Always add the last point of the centerline
        last_point = enu_centerline[-1]
        last_e = round(last_point[0], 6)
        last_n = round(last_point[1], 6)
        last_u = round(last_point[2], 6)
        
        # Check if we already added this point
        if not spawn_points or (spawn_points[-1]['position']['east'] != last_e or 
                                spawn_points[-1]['position']['north'] != last_n):
            # Calculate yaw from last segment
            if len(enu_centerline) >= 2:
                p1 = enu_centerline[-2]
                p2 = enu_centerline[-1]
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                yaw = math.atan2(dy, dx) if (dx != 0 or dy != 0) else 0.0
            else:
                yaw = 0.0
            
            spawn_point = {
                'id': spawn_id,
                'name': f'spawn_point_{spawn_id}',
                'position': {
                    'east': last_e,
                    'north': last_n,
                    'up': last_u
                },
                'orientation': {
                    'yaw': round(yaw, 6)
                },
                'way_id': centerline['way_id'],
                'road_name': centerline['name'],
                'highway_type': centerline['highway_type']
            }
            
            spawn_points.append(spawn_point)
            spawn_id += 1
    
    return spawn_points


def export_spawn_points_yaml(osm_file_path: str, output_path: str, spacing: float = 10.0) -> List[Dict]:
    """
    Export spawn_points.yaml with spawn points on roads.
    
    Args:
        osm_file_path: Path to OSM file
        output_path: Path to output YAML file
        spacing: Spacing between spawn points in meters (default: 10.0)
    
    Returns:
        List of spawn point dictionaries
    """
    # Create ENU projection
    enu_proj = create_enu_from_osm(osm_file_path)
    
    # Extract road metadata
    road_metadata = extract_road_metadata(osm_file_path)
    lane_centerlines = road_metadata['lane_centerlines']
    
    # Generate spawn points
    spawn_points = generate_spawn_points(lane_centerlines, enu_proj, spacing)
    
    # Create YAML structure
    yaml_data = {
        'spawn_points': spawn_points,
        'total_spawn_points': len(spawn_points),
        'projection_center': {
            'latitude': enu_proj.center_lat,
            'longitude': enu_proj.center_lon,
            'height': enu_proj.center_h
        }
    }
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    return spawn_points


def export_all_metadata(osm_file_path: str, roads_json_path: str, spawn_points_yaml_path: str,
                        spawn_spacing: float = 10.0) -> Tuple[Dict, List[Dict]]:
    """
    Export all metadata files (roads.json and spawn_points.yaml).
    
    Args:
        osm_file_path: Path to OSM file
        roads_json_path: Path to output roads.json file
        spawn_points_yaml_path: Path to output spawn_points.yaml file
        spawn_spacing: Spacing between spawn points in meters (default: 10.0)
    
    Returns:
        Tuple of (roads_data, spawn_points)
    """
    # Export roads.json
    roads_data = export_roads_json(osm_file_path, roads_json_path)
    
    # Export spawn_points.yaml
    spawn_points = export_spawn_points_yaml(osm_file_path, spawn_points_yaml_path, spawn_spacing)
    
    return roads_data, spawn_points

