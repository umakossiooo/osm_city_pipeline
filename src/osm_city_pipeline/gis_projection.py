"""GIS projection utilities for OSM to ENU coordinate conversion."""

import xml.etree.ElementTree as ET
import math
from typing import Tuple, Optional
from pyproj import Transformer, CRS, Geod


class ENUProjection:
    """East-North-Up (ENU) projection centered at a reference point."""
    
    def __init__(self, center_lat: float, center_lon: float, center_h: float = 0.0):
        """
        Initialize ENU projection centered at given coordinates.
        
        Args:
            center_lat: Latitude of the projection center (degrees)
            center_lon: Longitude of the projection center (degrees)
            center_h: Height of the projection center (meters, default: 0.0)
        """
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.center_h = center_h
        
        # Create WGS84 geodetic CRS
        wgs84 = CRS.from_epsg(4326)
        
        # Create local ENU coordinate system using Transverse Mercator
        # centered at the reference point with scale factor 1.0
        # This gives us East-North coordinates in meters
        enu_crs_string = (
            f"+proj=tmerc +lat_0={center_lat} +lon_0={center_lon} "
            f"+k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"
        )
        enu_crs = CRS.from_string(enu_crs_string)
        
        # Create transformer from WGS84 to ENU
        self.transformer = Transformer.from_crs(
            wgs84, enu_crs, always_xy=True
        )
        
        # Create geodetic calculator for accurate distance/azimuth calculations
        self.geod = Geod(ellps='WGS84')
    
    def project_to_enu(self, lat: float, lon: float, h: float = 0.0) -> Tuple[float, float, float]:
        """
        Project WGS84 coordinates to ENU (East-North-Up) coordinates.
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            h: Height in meters (default: 0.0)
        
        Returns:
            Tuple of (east, north, up) coordinates in meters
        """
        # Transform to local coordinates (x = east, y = north)
        east, north = self.transformer.transform(lon, lat)
        
        # Calculate height difference (up component)
        up = h - self.center_h
        
        # Return (east, north, up)
        return (east, north, up)


def get_osm_bounds(osm_file_path: str) -> Optional[Tuple[float, float, float, float]]:
    """
    Extract bounding box from OSM file.
    
    Args:
        osm_file_path: Path to the OSM XML file
    
    Returns:
        Tuple of (minlat, minlon, maxlat, maxlon) or None if not found
    """
    try:
        tree = ET.parse(osm_file_path)
        root = tree.getroot()
        
        # Look for bounds element
        bounds = root.find('bounds')
        if bounds is not None:
            minlat = float(bounds.get('minlat'))
            minlon = float(bounds.get('minlon'))
            maxlat = float(bounds.get('maxlat'))
            maxlon = float(bounds.get('maxlon'))
            return (minlat, minlon, maxlat, maxlon)
        
        # If no bounds element, calculate from nodes
        nodes = root.findall('node')
        if not nodes:
            return None
        
        lats = [float(node.get('lat')) for node in nodes if node.get('lat')]
        lons = [float(node.get('lon')) for node in nodes if node.get('lon')]
        
        if not lats or not lons:
            return None
        
        return (min(lats), min(lons), max(lats), max(lons))
    
    except Exception as e:
        print(f"Error parsing OSM file: {e}")
        return None


def create_enu_from_osm(osm_file_path: str, center_h: float = 0.0) -> Optional[ENUProjection]:
    """
    Create ENU projection centered at the bounding box center of an OSM file.
    
    Args:
        osm_file_path: Path to the OSM XML file
        center_h: Height of the projection center in meters (default: 0.0)
    
    Returns:
        ENUProjection instance or None if bounds cannot be determined
    """
    bounds = get_osm_bounds(osm_file_path)
    if bounds is None:
        return None
    
    minlat, minlon, maxlat, maxlon = bounds
    
    # Calculate center point
    center_lat = (minlat + maxlat) / 2.0
    center_lon = (minlon + maxlon) / 2.0
    
    return ENUProjection(center_lat, center_lon, center_h)


# Convenience function matching the required signature
def project_to_enu(lat: float, lon: float, h: float = 0.0, 
                   center_lat: Optional[float] = None,
                   center_lon: Optional[float] = None,
                   osm_file_path: Optional[str] = None) -> Tuple[float, float, float]:
    """
    Project WGS84 coordinates to ENU coordinates.
    
    This function can work in two modes:
    1. If osm_file_path is provided, uses the OSM file's bounding box center
    2. If center_lat and center_lon are provided, uses those as the center
    3. Otherwise, uses the provided coordinates as the center (identity projection)
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        h: Height in meters (default: 0.0)
        center_lat: Latitude of projection center (optional)
        center_lon: Longitude of projection center (optional)
        osm_file_path: Path to OSM file to extract bounds from (optional)
    
    Returns:
        Tuple of (east, north, up) coordinates in meters
    """
    if osm_file_path:
        enu_proj = create_enu_from_osm(osm_file_path)
        if enu_proj is None:
            raise ValueError(f"Could not determine bounds from OSM file: {osm_file_path}")
        return enu_proj.project_to_enu(lat, lon, h)
    elif center_lat is not None and center_lon is not None:
        enu_proj = ENUProjection(center_lat, center_lon)
        return enu_proj.project_to_enu(lat, lon, h)
    else:
        # Default: use the point itself as center (identity projection)
        return (0.0, 0.0, h)

