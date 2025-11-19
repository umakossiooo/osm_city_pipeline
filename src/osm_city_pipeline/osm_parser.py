"""OSM file parser using osmium."""

import osmium
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class OSMHandler(osmium.SimpleHandler):
    """Handler for parsing OSM files."""
    
    def __init__(self):
        super().__init__()
        self.nodes = {}  # node_id -> (lat, lon)
        self.ways = {}  # way_id -> {nodes: [node_ids], tags: {tag_key: tag_value}}
        self.relations = {}  # relation_id -> {members: [...], tags: {...}}
        self.node_tags = {}  # node_id -> {tag_key: tag_value}
    
    def node(self, n):
        """Process a node."""
        self.nodes[n.id] = (n.location.lat, n.location.lon)
        
        # Store node tags if any
        if len(list(n.tags)) > 0:
            tags = {}
            for tag in n.tags:
                tags[tag.k] = tag.v
            self.node_tags[n.id] = tags
    
    def way(self, w):
        """Process a way."""
        node_ids = [n.ref for n in w.nodes]
        
        # Only store ways with at least 2 nodes
        if len(node_ids) < 2:
            return
        
        tags = {}
        for tag in w.tags:
            tags[tag.k] = tag.v
        
        self.ways[w.id] = {
            'nodes': node_ids,
            'tags': tags
        }
    
    def relation(self, r):
        """Process a relation."""
        members = []
        for m in r.members:
            # m.type is an enum-like object, convert to string
            try:
                member_type = m.type.name.lower()
            except AttributeError:
                member_type = str(m.type).lower()
            members.append({
                'type': member_type,
                'ref': m.ref,
                'role': m.role
            })
        
        tags = {}
        for tag in r.tags:
            tags[tag.k] = tag.v
        
        self.relations[r.id] = {
            'members': members,
            'tags': tags
        }


def parse_osm_file(osm_file_path: str) -> Tuple[Dict, Dict, Dict]:
    """
    Parse an OSM file and return nodes, ways, and relations.
    
    Args:
        osm_file_path: Path to the OSM file
    
    Returns:
        Tuple of (nodes_dict, ways_dict, relations_dict)
    """
    handler = OSMHandler()
    
    try:
        handler.apply_file(osm_file_path, locations=True)
    except Exception as e:
        raise ValueError(f"Error parsing OSM file {osm_file_path}: {e}")
    
    return handler.nodes, handler.ways, handler.relations


def get_node_coordinates(node_id: int, nodes: Dict) -> Optional[Tuple[float, float]]:
    """
    Get coordinates for a node ID.
    
    Args:
        node_id: Node ID
        nodes: Nodes dictionary from parse_osm_file
    
    Returns:
        Tuple of (lat, lon) or None if not found
    """
    return nodes.get(node_id)


def get_way_coordinates(way_id: int, ways: Dict, nodes: Dict) -> Optional[List[Tuple[float, float]]]:
    """
    Get list of coordinates for a way.
    
    Args:
        way_id: Way ID
        ways: Ways dictionary from parse_osm_file
        nodes: Nodes dictionary from parse_osm_file
    
    Returns:
        List of (lat, lon) tuples or None if way not found
    """
    if way_id not in ways:
        return None
    
    way = ways[way_id]
    coordinates = []
    
    for node_id in way['nodes']:
        coords = get_node_coordinates(node_id, nodes)
        if coords is not None:
            coordinates.append(coords)
    
    return coordinates if len(coordinates) > 0 else None

