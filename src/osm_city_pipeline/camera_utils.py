"""Camera utilities for positioning and visualization."""

from typing import Tuple, Optional
import math

from .gis_projection import ENUProjection


def calculate_camera_pose(center_east: float, center_north: float, center_up: float,
                         distance: float = 50.0, pitch: float = 1.57) -> Tuple[float, float, float, float, float, float]:
    """
    Calculate camera pose looking at a point from above.
    
    Args:
        center_east: East coordinate of target point
        center_north: North coordinate of target point
        center_up: Up coordinate of target point
        distance: Distance from target (default: 50.0m)
        pitch: Pitch angle in radians (default: 1.57 = 90 degrees, looking down)
    
    Returns:
        Tuple of (x, y, z, roll, pitch, yaw) for camera pose
    """
    # Camera positioned directly above the target
    x = center_east
    y = center_north
    z = center_up + distance
    
    roll = 0.0
    yaw = 0.0  # Looking north by default
    
    return (x, y, z, roll, pitch, yaw)


def calculate_camera_pose_for_spawn_point(spawn_east: float, spawn_north: float, spawn_up: float,
                                         spawn_yaw: float, distance: float = 10.0,
                                         height: float = 5.0) -> Tuple[float, float, float, float, float, float]:
    """
    Calculate camera pose looking at a spawn point from behind and above.
    
    Args:
        spawn_east: East coordinate of spawn point
        spawn_north: North coordinate of spawn point
        spawn_up: Up coordinate of spawn point
        spawn_yaw: Yaw orientation of spawn point
        distance: Distance behind spawn point (default: 10.0m)
        height: Height above spawn point (default: 5.0m)
    
    Returns:
        Tuple of (x, y, z, roll, pitch, yaw) for camera pose
    """
    # Position camera behind spawn point
    x = spawn_east - distance * math.cos(spawn_yaw)
    y = spawn_north - distance * math.sin(spawn_yaw)
    z = spawn_up + height
    
    roll = 0.0
    pitch = 0.3  # Slight downward angle
    yaw = spawn_yaw  # Camera looks in same direction as spawn point
    
    return (x, y, z, roll, pitch, yaw)


def get_world_center_camera_pose(enu_proj: ENUProjection, distance: float = 50.0) -> Tuple[float, float, float, float, float, float]:
    """
    Get camera pose at world center looking down.
    
    Args:
        enu_proj: ENU projection instance
        distance: Height above center (default: 50.0m)
    
    Returns:
        Tuple of (x, y, z, roll, pitch, yaw) for camera pose
    """
    return calculate_camera_pose(0.0, 0.0, 0.0, distance, pitch=1.57)

