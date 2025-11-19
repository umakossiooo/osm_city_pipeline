"""Debug tools for generating SDF markers for verification."""

from typing import List, Dict, Tuple, Optional
from xml.etree import ElementTree as ET
from xml.dom import minidom
import math

from .gis_projection import create_enu_from_osm, ENUProjection


def create_marker_model(name: str, position: Tuple[float, float, float],
                       color: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 1.0),
                       size: float = 0.5) -> ET.Element:
    """
    Create a simple marker model (sphere) for visualization.
    
    Args:
        name: Model name
        position: (east, north, up) position
        color: RGBA color (default: red)
        size: Sphere radius (default: 0.5m)
    
    Returns:
        Model element
    """
    model = ET.Element('model', name=name)
    
    static = ET.SubElement(model, 'static')
    static.text = 'true'
    
    pose = ET.SubElement(model, 'pose')
    pose.text = f'{position[0]} {position[1]} {position[2]} 0 0 0'
    
    link = ET.SubElement(model, 'link', name='link')
    
    # Visual
    visual = ET.SubElement(link, 'visual', name='visual')
    geometry = ET.SubElement(visual, 'geometry')
    sphere = ET.SubElement(geometry, 'sphere')
    radius = ET.SubElement(sphere, 'radius')
    radius.text = str(size)
    
    material = ET.SubElement(visual, 'material')
    script = ET.SubElement(material, 'script')
    script_name = ET.SubElement(script, 'name')
    script_name.text = 'Gazebo/Red'
    uri = ET.SubElement(script, 'uri')
    uri.text = 'file://media/materials/scripts/gazebo.material'
    ambient = ET.SubElement(material, 'ambient')
    ambient.text = f'{color[0]} {color[1]} {color[2]} {color[3]}'
    
    # Collision
    collision = ET.SubElement(link, 'collision', name='collision')
    geometry_coll = ET.SubElement(collision, 'geometry')
    sphere_coll = ET.SubElement(geometry_coll, 'sphere')
    radius_coll = ET.SubElement(sphere_coll, 'radius')
    radius_coll.text = str(size)
    
    return model


def create_arrow_marker(name: str, position: Tuple[float, float, float],
                        yaw: float, length: float = 2.0,
                        color: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 1.0)) -> ET.Element:
    """
    Create an arrow marker showing direction (yaw).
    
    Args:
        name: Model name
        position: (east, north, up) position
        yaw: Yaw angle in radians
        length: Arrow length (default: 2.0m)
        color: RGBA color (default: green)
    
    Returns:
        Model element
    """
    model = ET.Element('model', name=name)
    
    static = ET.SubElement(model, 'static')
    static.text = 'true'
    
    pose = ET.SubElement(model, 'pose')
    pose.text = f'{position[0]} {position[1]} {position[2]} 0 0 {yaw}'
    
    link = ET.SubElement(model, 'link', name='link')
    
    # Visual - cylinder for arrow shaft
    visual = ET.SubElement(link, 'visual', name='visual')
    geometry = ET.SubElement(visual, 'geometry')
    cylinder = ET.SubElement(geometry, 'cylinder')
    radius = ET.SubElement(cylinder, 'radius')
    radius.text = '0.1'
    length_elem = ET.SubElement(cylinder, 'length')
    length_elem.text = str(length)
    
    material = ET.SubElement(visual, 'material')
    script = ET.SubElement(material, 'script')
    script_name = ET.SubElement(script, 'name')
    script_name.text = 'Gazebo/Green'
    uri = ET.SubElement(script, 'uri')
    uri.text = 'file://media/materials/scripts/gazebo.material'
    ambient = ET.SubElement(material, 'ambient')
    ambient.text = f'{color[0]} {color[1]} {color[2]} {color[3]}'
    
    return model


def create_camera_marker(name: str, camera_pose: Tuple[float, float, float, float, float, float],
                        color: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)) -> ET.Element:
    """
    Create a camera marker at the specified pose.
    
    Args:
        name: Model name
        camera_pose: (x, y, z, roll, pitch, yaw) camera pose
        color: RGBA color (default: blue)
    
    Returns:
        Model element
    """
    x, y, z, roll, pitch, yaw = camera_pose
    
    model = ET.Element('model', name=name)
    
    static = ET.SubElement(model, 'static')
    static.text = 'true'
    
    pose = ET.SubElement(model, 'pose')
    pose.text = f'{x} {y} {z} {roll} {pitch} {yaw}'
    
    link = ET.SubElement(model, 'link', name='link')
    
    # Visual - box for camera representation
    visual = ET.SubElement(link, 'visual', name='visual')
    geometry = ET.SubElement(visual, 'geometry')
    box = ET.SubElement(geometry, 'box')
    size = ET.SubElement(box, 'size')
    size.text = '0.3 0.3 0.3'
    
    material = ET.SubElement(visual, 'material')
    script = ET.SubElement(material, 'script')
    script_name = ET.SubElement(script, 'name')
    script_name.text = 'Gazebo/Blue'
    uri = ET.SubElement(script, 'uri')
    uri.text = 'file://media/materials/scripts/gazebo.material'
    ambient = ET.SubElement(material, 'ambient')
    ambient.text = f'{color[0]} {color[1]} {color[2]} {color[3]}'
    
    return model


def generate_debug_camera_sdf(osm_file_path: str, output_path: str,
                               camera_pose: Optional[Tuple[float, float, float, float, float, float]] = None) -> str:
    """
    Generate SDF file with camera marker for debugging.
    
    Args:
        osm_file_path: Path to OSM file
        output_path: Path to output SDF file
        camera_pose: Optional camera pose (x, y, z, roll, pitch, yaw). If None, uses world center.
    
    Returns:
        Path to generated SDF file
    """
    from pathlib import Path
    
    # Create ENU projection
    enu_proj = create_enu_from_osm(osm_file_path)
    
    # Determine camera pose
    if camera_pose is None:
        from .camera_utils import get_world_center_camera_pose
        camera_pose = get_world_center_camera_pose(enu_proj)
    
    # Create SDF structure
    sdf = ET.Element('sdf', version='1.11')
    world = ET.SubElement(sdf, 'world', name='debug_camera')
    
    # Add physics
    physics = ET.SubElement(world, 'physics', type='ode')
    gravity = ET.SubElement(physics, 'gravity')
    gravity.text = '0 0 -9.81'
    
    # Add scene
    scene = ET.SubElement(world, 'scene')
    ambient = ET.SubElement(scene, 'ambient')
    ambient.text = '0.4 0.4 0.4 1'
    background = ET.SubElement(scene, 'background')
    background.text = '0.7 0.7 0.7 1'
    
    # Add ground plane
    ground = ET.SubElement(world, 'model', name='ground_plane')
    static = ET.SubElement(ground, 'static')
    static.text = 'true'
    link = ET.SubElement(ground, 'link', name='link')
    collision = ET.SubElement(link, 'collision', name='collision')
    geometry_coll = ET.SubElement(collision, 'geometry')
    plane_coll = ET.SubElement(geometry_coll, 'plane')
    normal = ET.SubElement(plane_coll, 'normal')
    normal.text = '0 0 1'
    size = ET.SubElement(plane_coll, 'size')
    size.text = '1000 1000'
    visual = ET.SubElement(link, 'visual', name='visual')
    geometry_vis = ET.SubElement(visual, 'geometry')
    plane_vis = ET.SubElement(geometry_vis, 'plane')
    normal_vis = ET.SubElement(plane_vis, 'normal')
    normal_vis.text = '0 0 1'
    size_vis = ET.SubElement(plane_vis, 'size')
    size_vis.text = '1000 1000'
    
    # Add camera marker
    camera_marker = create_camera_marker('camera_marker', camera_pose)
    world.append(camera_marker)
    
    # Add GUI with camera
    gui = ET.SubElement(world, 'gui')
    camera_gui = ET.SubElement(gui, 'camera', name='user_camera')
    pose_camera = ET.SubElement(camera_gui, 'pose')
    pose_camera.text = f'{camera_pose[0]} {camera_pose[1]} {camera_pose[2]} {camera_pose[3]} {camera_pose[4]} {camera_pose[5]}'
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Format XML
    xml_str = ET.tostring(sdf, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    return str(output_file)


def generate_debug_spawn_sdf(spawn_points_yaml_path: str, output_path: str,
                            spawn_ids: Optional[List[int]] = None,
                            max_spawn_points: int = 50) -> str:
    """
    Generate SDF file with spawn point markers for debugging.
    
    Args:
        spawn_points_yaml_path: Path to spawn_points.yaml file
        output_path: Path to output SDF file
        spawn_ids: Optional list of specific spawn point IDs to visualize. If None, shows first N points.
        max_spawn_points: Maximum number of spawn points to visualize (default: 50)
    
    Returns:
        Path to generated SDF file
    """
    import yaml
    from pathlib import Path
    
    # Load spawn points
    with open(spawn_points_yaml_path, 'r') as f:
        spawn_data = yaml.safe_load(f)
    
    spawn_points = spawn_data['spawn_points']
    
    # Filter spawn points
    if spawn_ids is not None:
        filtered_points = [sp for sp in spawn_points if sp['id'] in spawn_ids]
    else:
        filtered_points = spawn_points[:max_spawn_points]
    
    # Create SDF structure
    sdf = ET.Element('sdf', version='1.11')
    world = ET.SubElement(sdf, 'world', name='debug_spawn')
    
    # Add physics
    physics = ET.SubElement(world, 'physics', type='ode')
    gravity = ET.SubElement(physics, 'gravity')
    gravity.text = '0 0 -9.81'
    
    # Add scene
    scene = ET.SubElement(world, 'scene')
    ambient = ET.SubElement(scene, 'ambient')
    ambient.text = '0.4 0.4 0.4 1'
    background = ET.SubElement(scene, 'background')
    background.text = '0.7 0.7 0.7 1'
    
    # Add ground plane
    ground = ET.SubElement(world, 'model', name='ground_plane')
    static = ET.SubElement(ground, 'static')
    static.text = 'true'
    link = ET.SubElement(ground, 'link', name='link')
    collision = ET.SubElement(link, 'collision', name='collision')
    geometry_coll = ET.SubElement(collision, 'geometry')
    plane_coll = ET.SubElement(geometry_coll, 'plane')
    normal = ET.SubElement(plane_coll, 'normal')
    normal.text = '0 0 1'
    size = ET.SubElement(plane_coll, 'size')
    size.text = '1000 1000'
    visual = ET.SubElement(link, 'visual', name='visual')
    geometry_vis = ET.SubElement(visual, 'geometry')
    plane_vis = ET.SubElement(geometry_vis, 'plane')
    normal_vis = ET.SubElement(plane_vis, 'normal')
    normal_vis.text = '0 0 1'
    size_vis = ET.SubElement(plane_vis, 'size')
    size_vis.text = '1000 1000'
    
    # Add spawn point markers
    for sp in filtered_points:
        pos = sp['position']
        position = (pos['east'], pos['north'], pos['up'])
        
        # Create marker sphere
        marker = create_marker_model(f'spawn_marker_{sp["id"]}', position,
                                    color=(1.0, 0.0, 0.0, 1.0), size=0.3)
        world.append(marker)
        
        # Create arrow showing direction
        if 'orientation' in sp and 'yaw' in sp['orientation']:
            yaw = sp['orientation']['yaw']
            arrow = create_arrow_marker(f'spawn_arrow_{sp["id"]}', position, yaw,
                                       length=1.0, color=(0.0, 1.0, 0.0, 1.0))
            world.append(arrow)
    
    # Add GUI with camera at first spawn point
    if filtered_points:
        first_sp = filtered_points[0]
        pos = first_sp['position']
        from .camera_utils import calculate_camera_pose_for_spawn_point
        yaw = first_sp.get('orientation', {}).get('yaw', 0.0)
        camera_pose = calculate_camera_pose_for_spawn_point(
            pos['east'], pos['north'], pos['up'], yaw
        )
        
        gui = ET.SubElement(world, 'gui')
        camera_gui = ET.SubElement(gui, 'camera', name='user_camera')
        pose_camera = ET.SubElement(camera_gui, 'pose')
        pose_camera.text = f'{camera_pose[0]} {camera_pose[1]} {camera_pose[2]} {camera_pose[3]} {camera_pose[4]} {camera_pose[5]}'
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Format XML
    xml_str = ET.tostring(sdf, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    return str(output_file)

