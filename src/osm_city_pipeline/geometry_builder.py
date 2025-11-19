"""Build 3D geometry from ENU coordinates for Gazebo."""

from typing import Dict, List, Tuple, Optional
import math

from .gis_projection import ENUProjection
from .road_extractor import extract_road_metadata
from .osm_parser import parse_osm_file, get_way_coordinates


def build_road_geometry(highway: Dict, enu_proj: ENUProjection, width: float = 5.0) -> Dict:
    """
    Build 3D geometry for a road from highway data.
    
    Args:
        highway: Highway dictionary with coordinates
        enu_proj: ENU projection instance
        width: Road width in meters (default: 5.0)
    
    Returns:
        Dictionary with geometry data:
        - type: 'road'
        - vertices: List of (x, y, z) tuples in ENU coordinates
        - width: Road width
    """
    vertices = []
    
    for lat, lon in highway['coordinates']:
        e, n, u = enu_proj.project_to_enu(lat, lon, 0.0)
        vertices.append((e, n, u))
    
    return {
        'type': 'road',
        'way_id': highway['way_id'],
        'name': highway.get('name', ''),
        'highway_type': highway.get('highway_type', ''),
        'vertices': vertices,
        'width': width
    }


def build_building_geometry(building: Dict, enu_proj: ENUProjection, height: float = 10.0) -> Dict:
    """
    Build 3D geometry for a building from building data.
    
    Args:
        building: Building dictionary with coordinates
        enu_proj: ENU projection instance
        height: Building height in meters (default: 10.0)
    
    Returns:
        Dictionary with geometry data:
        - type: 'building'
        - base_vertices: List of (x, y, z) tuples for base polygon
        - height: Building height
    """
    base_vertices = []
    
    for lat, lon in building['coordinates']:
        e, n, u = enu_proj.project_to_enu(lat, lon, 0.0)
        base_vertices.append((e, n, u))
    
    return {
        'type': 'building',
        'way_id': building.get('way_id', ''),
        'base_vertices': base_vertices,
        'height': height
    }


def build_park_geometry(park: Dict, enu_proj: ENUProjection) -> Dict:
    """
    Build 3D geometry for a park from park data.
    
    Args:
        park: Park dictionary with coordinates
        enu_proj: ENU projection instance
    
    Returns:
        Dictionary with geometry data:
        - type: 'park'
        - vertices: List of (x, y, z) tuples for park polygon
    """
    vertices = []
    
    for lat, lon in park['coordinates']:
        e, n, u = enu_proj.project_to_enu(lat, lon, 0.0)
        vertices.append((e, n, u))
    
    return {
        'type': 'park',
        'way_id': park.get('way_id', ''),
        'vertices': vertices
    }


def build_sidewalk_geometry(highway: Dict, enu_proj: ENUProjection, width: float = 1.5) -> Dict:
    """
    Build 3D geometry for sidewalks along a highway.
    
    Args:
        highway: Highway dictionary with coordinates
        enu_proj: ENU projection instance
        width: Sidewalk width in meters (default: 1.5)
    
    Returns:
        Dictionary with geometry data:
        - type: 'sidewalk'
        - vertices: List of (x, y, z) tuples
        - width: Sidewalk width
    """
    vertices = []
    
    for lat, lon in highway['coordinates']:
        e, n, u = enu_proj.project_to_enu(lat, lon, 0.0)
        vertices.append((e, n, u))
    
    return {
        'type': 'sidewalk',
        'way_id': highway['way_id'],
        'vertices': vertices,
        'width': width
    }


def extract_buildings(osm_file_path: str) -> List[Dict]:
    """
    Extract buildings from OSM file (both ways and relations).
    
    Args:
        osm_file_path: Path to OSM file
    
    Returns:
        List of building dictionaries
    """
    nodes, ways, relations = parse_osm_file(osm_file_path)
    
    buildings = []
    processed_way_ids = set()  # Track ways already processed from relations
    
    # First, process building relations (multipolygons)
    for rel_id, rel_data in relations.items():
        tags = rel_data['tags']
        
        # Check if it's a building relation
        if 'building' in tags or tags.get('type') == 'multipolygon':
            # Extract outer ways from relation
            for member in rel_data['members']:
                if member['type'] == 'way' and member['role'] in ['outer', '']:
                    way_id = member['ref']
                    if way_id in ways:
                        processed_way_ids.add(way_id)
                        coordinates = get_way_coordinates(way_id, {way_id: ways[way_id]}, nodes)
                        if coordinates and len(coordinates) >= 3:
                            # Merge tags from relation and way
                            way_tags = ways[way_id]['tags'].copy()
                            way_tags.update(tags)  # Relation tags take precedence
                            buildings.append({
                                'way_id': way_id,
                                'relation_id': rel_id,
                                'coordinates': coordinates,
                                'tags': way_tags
                            })
    
    # Then, process standalone building ways (not in relations)
    for way_id, way_data in ways.items():
        if way_id in processed_way_ids:
            continue  # Already processed from relation
        
        tags = way_data['tags']
        
        # Check if it's a building
        if 'building' in tags or tags.get('building:part') or tags.get('building:levels'):
            coordinates = get_way_coordinates(way_id, {way_id: way_data}, nodes)
            if coordinates and len(coordinates) >= 3:  # At least 3 points for a polygon
                buildings.append({
                    'way_id': way_id,
                    'coordinates': coordinates,
                    'tags': tags
                })
    
    return buildings


def extract_parks(osm_file_path: str) -> List[Dict]:
    """
    Extract parks and green areas from OSM file.
    
    Args:
        osm_file_path: Path to OSM file
    
    Returns:
        List of park dictionaries
    """
    nodes, ways, relations = parse_osm_file(osm_file_path)
    
    parks = []
    
    # Check ways for leisure areas
    for way_id, way_data in ways.items():
        tags = way_data['tags']
        
        if tags.get('leisure') in ['park', 'garden', 'recreation_ground'] or \
           tags.get('landuse') in ['grass', 'forest', 'meadow']:
            coordinates = get_way_coordinates(way_id, {way_id: way_data}, nodes)
            if coordinates and len(coordinates) >= 3:
                parks.append({
                    'way_id': way_id,
                    'coordinates': coordinates,
                    'tags': tags
                })
    
    # Check relations for multipolygon parks
    for rel_id, rel_data in relations.items():
        tags = rel_data['tags']
        
        if tags.get('leisure') in ['park', 'garden'] or \
           tags.get('landuse') in ['grass', 'forest', 'meadow']:
            # For now, skip relations (would need more complex handling)
            pass
    
    return parks


def build_all_geometry(osm_file_path: str, enu_proj: ENUProjection) -> Dict:
    """
    Build all geometry from OSM file using ENU projection.
    
    Args:
        osm_file_path: Path to OSM file
        enu_proj: ENU projection instance
    
    Returns:
        Dictionary containing:
        - roads: List of road geometries
        - buildings: List of building geometries
        - parks: List of park geometries
        - sidewalks: List of sidewalk geometries
    """
    # Extract road metadata
    road_metadata = extract_road_metadata(osm_file_path)
    highways = road_metadata['highways']
    
    # Extract buildings
    buildings = extract_buildings(osm_file_path)
    
    # Extract parks
    parks = extract_parks(osm_file_path)
    
    # Build geometries
    road_geometries = []
    for highway in highways:
        road_geom = build_road_geometry(highway, enu_proj)
        road_geometries.append(road_geom)
    
    building_geometries = []
    for building in buildings:
        # Get height from tags if available
        height = 10.0  # default
        if 'building:levels' in building['tags']:
            try:
                levels = int(building['tags']['building:levels'])
                height = levels * 3.0  # ~3m per floor
            except (ValueError, TypeError):
                pass
        
        building_geom = build_building_geometry(building, enu_proj, height)
        building_geometries.append(building_geom)
    
    park_geometries = []
    for park in parks:
        park_geom = build_park_geometry(park, enu_proj)
        park_geometries.append(park_geom)
    
    sidewalk_geometries = []
    for highway in highways:
        # Only add sidewalks to major roads
        if highway['highway_type'] in ['primary', 'secondary', 'tertiary', 'residential']:
            sidewalk_geom = build_sidewalk_geometry(highway, enu_proj)
            sidewalk_geometries.append(sidewalk_geom)
    
    return {
        'roads': road_geometries,
        'buildings': building_geometries,
        'parks': park_geometries,
        'sidewalks': sidewalk_geometries
    }

