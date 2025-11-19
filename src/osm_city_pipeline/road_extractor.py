"""Extract roads, highways, intersections, and lane centerlines from OSM data."""

import json
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from pathlib import Path

from .osm_parser import parse_osm_file, get_way_coordinates


# Highway types to extract (ordered by importance/priority)
HIGHWAY_TYPES = [
    'motorway', 'motorway_link',
    'trunk', 'trunk_link',
    'primary', 'primary_link',
    'secondary', 'secondary_link',
    'tertiary', 'tertiary_link',
    'unclassified',
    'residential',
    'service',
    'living_street'
]


def is_highway(way_tags: Dict[str, str]) -> bool:
    """
    Check if a way is a highway/road.
    
    Args:
        way_tags: Dictionary of way tags
    
    Returns:
        True if the way is a highway
    """
    highway = way_tags.get('highway', '').lower()
    return highway in HIGHWAY_TYPES


def extract_highways(osm_file_path: str) -> List[Dict]:
    """
    Extract all highways from an OSM file.
    
    Args:
        osm_file_path: Path to the OSM file
    
    Returns:
        List of highway dictionaries with keys:
        - way_id: OSM way ID
        - name: Road name (if available)
        - highway_type: Type of highway
        - coordinates: List of (lat, lon) tuples
        - tags: All way tags
    """
    nodes, ways, relations = parse_osm_file(osm_file_path)
    
    highways = []
    
    for way_id, way_data in ways.items():
        tags = way_data['tags']
        
        if not is_highway(tags):
            continue
        
        # Get coordinates for this way
        coordinates = get_way_coordinates(way_id, {way_id: way_data}, nodes)
        if coordinates is None or len(coordinates) < 2:
            continue
        
        highway = {
            'way_id': way_id,
            'name': tags.get('name', ''),
            'highway_type': tags.get('highway', ''),
            'coordinates': coordinates,
            'tags': tags
        }
        
        highways.append(highway)
    
    return highways


def find_intersections(highways: List[Dict], nodes: Dict) -> List[Dict]:
    """
    Find intersections where highways meet.
    
    Args:
        highways: List of highway dictionaries from extract_highways
        nodes: Nodes dictionary from parse_osm_file
    
    Returns:
        List of intersection dictionaries with keys:
        - node_id: OSM node ID
        - coordinates: (lat, lon) tuple
        - connected_ways: List of way IDs connected at this intersection
    """
    # Count how many ways pass through each node
    node_way_count = defaultdict(list)
    
    for highway in highways:
        way_id = highway['way_id']
        coordinates = highway['coordinates']
        
        # Find node IDs for coordinates (approximate matching)
        for coord in coordinates:
            # Find the closest node to this coordinate
            for node_id, (lat, lon) in nodes.items():
                if abs(lat - coord[0]) < 0.00001 and abs(lon - coord[1]) < 0.00001:
                    node_way_count[node_id].append(way_id)
                    break
    
    # Intersections are nodes where 2+ ways meet
    intersections = []
    for node_id, way_ids in node_way_count.items():
        if len(set(way_ids)) >= 2:  # At least 2 different ways
            coords = nodes.get(node_id)
            if coords:
                intersections.append({
                    'node_id': node_id,
                    'coordinates': coords,
                    'connected_ways': list(set(way_ids))
                })
    
    return intersections


def extract_lane_centerlines(highways: List[Dict]) -> List[Dict]:
    """
    Extract lane centerlines from highways.
    
    For now, this uses the highway centerline as the lane centerline.
    In future phases, this could be enhanced to handle multiple lanes.
    
    Args:
        highways: List of highway dictionaries from extract_highways
    
    Returns:
        List of lane centerline dictionaries with keys:
        - way_id: OSM way ID
        - name: Road name
        - centerline: List of (lat, lon) tuples
        - highway_type: Type of highway
        - lanes: Number of lanes (if specified in tags)
    """
    centerlines = []
    
    for highway in highways:
        # Get number of lanes from tags
        lanes_tag = highway['tags'].get('lanes', '')
        try:
            lanes = int(lanes_tag) if lanes_tag else 1
        except ValueError:
            lanes = 1
        
        centerline = {
            'way_id': highway['way_id'],
            'name': highway['name'],
            'centerline': highway['coordinates'],
            'highway_type': highway['highway_type'],
            'lanes': lanes
        }
        
        centerlines.append(centerline)
    
    return centerlines


def extract_road_metadata(osm_file_path: str) -> Dict:
    """
    Extract all road-related metadata from an OSM file.
    
    Args:
        osm_file_path: Path to the OSM file
    
    Returns:
        Dictionary containing:
        - highways: List of highway dictionaries
        - intersections: List of intersection dictionaries
        - lane_centerlines: List of lane centerline dictionaries
        - summary: Summary statistics
    """
    # Parse OSM file
    nodes, ways, relations = parse_osm_file(osm_file_path)
    
    # Extract highways
    highways = extract_highways(osm_file_path)
    
    # Find intersections
    intersections = find_intersections(highways, nodes)
    
    # Extract lane centerlines
    lane_centerlines = extract_lane_centerlines(highways)
    
    # Create summary
    highway_types = defaultdict(int)
    for hw in highways:
        highway_types[hw['highway_type']] += 1
    
    summary = {
        'total_highways': len(highways),
        'total_intersections': len(intersections),
        'total_lane_centerlines': len(lane_centerlines),
        'highway_types': dict(highway_types),
        'named_roads': sum(1 for hw in highways if hw['name']),
        'total_nodes': len(nodes),
        'total_ways': len(ways)
    }
    
    return {
        'highways': highways,
        'intersections': intersections,
        'lane_centerlines': lane_centerlines,
        'summary': summary
    }


def save_road_metadata(metadata: Dict, output_path: str) -> None:
    """
    Save road metadata to a JSON file.
    
    Args:
        metadata: Metadata dictionary from extract_road_metadata
        output_path: Path to output JSON file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def extract_and_save_road_metadata(osm_file_path: str, output_path: str) -> Dict:
    """
    Extract road metadata from OSM file and save to JSON.
    
    Args:
        osm_file_path: Path to the OSM file
        output_path: Path to output JSON file
    
    Returns:
        Metadata dictionary
    """
    metadata = extract_road_metadata(osm_file_path)
    save_road_metadata(metadata, output_path)
    return metadata

