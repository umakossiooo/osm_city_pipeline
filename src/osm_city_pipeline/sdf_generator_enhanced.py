"""Generate enhanced Gazebo Harmonic SDF world files using OSM2World mesh."""

from typing import Dict, List, Tuple, Optional
from xml.etree import ElementTree as ET
from xml.dom import minidom
from pathlib import Path
import os


def create_enhanced_sdf_world(
    osm_file_path: str,
    model_name: str,
    world_name: str = "osm_city",
    model_dir: Optional[str] = None,
    road_metadata: Optional[Dict] = None
) -> str:
    """
    Create enhanced SDF world XML using OSM2World mesh model.
    
    This preserves road coordinates from the original OSM file while using
    the detailed 3D mesh for visualization.
    
    Args:
        osm_file_path: Path to original OSM file (for metadata)
        model_name: Name of the mesh model
        world_name: Name of the world
        model_dir: Directory containing the model (default: models/<model_name>)
        road_metadata: Optional road metadata dictionary (preserves coordinates)
    
    Returns:
        SDF XML string
    """
    # Determine model directory
    if model_dir is None:
        script_dir = Path(__file__).parent.parent.parent
        model_dir = str(script_dir / "models" / model_name)
    
    model_path = Path(model_dir)
    if not model_path.exists():
        raise FileNotFoundError(f"Model directory not found: {model_dir}")
    
    # Create root element
    sdf = ET.Element('sdf', version='1.11')
    world = ET.SubElement(sdf, 'world', name=world_name)
    
    # Add physics (SDF 1.11 format)
    physics = ET.SubElement(world, 'physics')
    physics.set('type', 'ode')
    physics.set('name', 'default')
    max_step_size = ET.SubElement(physics, 'max_step_size')
    max_step_size.text = '0.001'
    real_time_factor = ET.SubElement(physics, 'real_time_factor')
    real_time_factor.text = '1.0'
    gravity_elem = ET.SubElement(physics, 'gravity')
    gravity_elem.text = '0 0 -9.81'
    
    # Add plugins (Gazebo Harmonic format)
    plugin_physics = ET.SubElement(world, 'plugin')
    plugin_physics.set('filename', 'gz-sim-physics-system')
    plugin_physics.set('name', 'gz::sim::systems::Physics')
    
    plugin_sensors = ET.SubElement(world, 'plugin')
    plugin_sensors.set('filename', 'gz-sim-sensors-system')
    plugin_sensors.set('name', 'gz::sim::systems::Sensors')
    render_engine = ET.SubElement(plugin_sensors, 'render_engine')
    render_engine.text = 'vulkan'
    
    plugin_scene = ET.SubElement(world, 'plugin')
    plugin_scene.set('filename', 'gz-sim-scene-broadcaster-system')
    plugin_scene.set('name', 'gz::sim::systems::SceneBroadcaster')
    
    plugin_user = ET.SubElement(world, 'plugin')
    plugin_user.set('filename', 'gz-sim-user-commands-system')
    plugin_user.set('name', 'gz::sim::systems::UserCommands')
    
    plugin_imu = ET.SubElement(world, 'plugin')
    plugin_imu.set('filename', 'gz-sim-imu-system')
    plugin_imu.set('name', 'gz::sim::systems::Imu')
    
    # Add scene
    scene = ET.SubElement(world, 'scene')
    ambient = ET.SubElement(scene, 'ambient')
    ambient.text = '0.4 0.4 0.4 1'
    background = ET.SubElement(scene, 'background')
    background.text = '0.7 0.7 0.7 1'
    shadows = ET.SubElement(scene, 'shadows')
    shadows.text = 'true'
    
    # Include the detailed mesh model
    include = ET.SubElement(world, 'include')
    name_elem = ET.SubElement(include, 'name')
    name_elem.text = model_name
    uri_elem = ET.SubElement(include, 'uri')
    uri_elem.text = f'model://{model_name}'
    
    # Pose transformation: OSM2World uses Y-up, Gazebo uses Z-up
    # Rotate 90° around X axis to convert Y-up to Z-up
    pose_elem = ET.SubElement(include, 'pose')
    pose_elem.text = '0 0 0 1.5708 0 0'
    
    # Add GUI with camera
    gui = ET.SubElement(world, 'gui')
    gui.set('fullscreen', '0')
    
    # Default camera (follow camera for robot)
    camera_follow = ET.SubElement(gui, 'camera')
    camera_follow.set('name', 'follow_camera')
    pose_cam = ET.SubElement(camera_follow, 'pose')
    pose_cam.text = '-8 0 4 0.4 0.6 0'
    view_controller = ET.SubElement(camera_follow, 'view_controller')
    view_controller.text = 'orbit'
    track_visual = ET.SubElement(camera_follow, 'track_visual')
    track_visual.text = 'saye::base_link::BaseVisual'
    
    # Default camera positioned to view the map
    camera_default = ET.SubElement(gui, 'camera')
    camera_default.set('name', 'default')
    pose_default = ET.SubElement(camera_default, 'pose')
    # Position camera above center, looking down
    pose_default.text = '0 0 50 0 -1.57 0'
    view_controller_default = ET.SubElement(camera_default, 'view_controller')
    view_controller_default.text = 'orbit'
    
    # Try to position camera on a road if road metadata is available
    if road_metadata and 'roads' in road_metadata and len(road_metadata['roads']) > 0:
        # Use first road's center point
        first_road = road_metadata['roads'][0]
        if 'center' in first_road:
            center = first_road['center']
            x = center.get('east', 0)
            y = center.get('north', 0)
            pose_default.text = f'{x} {y} 50 0 -1.57 0'
    
    # Note: Road coordinates are preserved in the metadata files
    # The mesh model provides visual detail, but road coordinates remain accurate
    # for navigation and robot spawning
    
    # Format XML
    xml_str = ET.tostring(sdf, encoding='unicode')
    reparsed = minidom.parseString(xml_str)
    return reparsed.toprettyxml(indent='  ')


def generate_enhanced_sdf_world(
    osm_file_path: str,
    output_path: str,
    model_name: str = "city_3d",
    world_name: str = "osm_city",
    use_osm2world: bool = True
) -> None:
    """
    Generate enhanced SDF world file using OSM2World mesh.
    
    Args:
        osm_file_path: Path to OSM file
        output_path: Path to output SDF file
        model_name: Name of the mesh model (default: city_3d)
        world_name: Name of the world (default: osm_city)
        use_osm2world: Whether to use OSM2World mesh (default: True)
    """
    script_dir = Path(__file__).parent.parent.parent
    model_dir = script_dir / "models" / model_name
    
    # Check if model exists
    if not model_dir.exists() and use_osm2world:
        raise FileNotFoundError(
            f"Model directory not found: {model_dir}\n"
            f"Please run: ./scripts/convert_with_osm2world.sh {osm_file_path} {model_name}"
        )
    
    # Load road metadata if available (for camera positioning)
    road_metadata = None
    maps_dir = script_dir / "maps"
    osm_stem = Path(osm_file_path).stem
    roads_file = maps_dir / f"{osm_stem}_roads.json"
    
    if roads_file.exists():
        import json
        try:
            with open(roads_file, 'r') as f:
                road_metadata = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load road metadata: {e}")
    
    # Generate SDF
    if use_osm2world and model_dir.exists():
        sdf_xml = create_enhanced_sdf_world(
            osm_file_path,
            model_name,
            world_name,
            str(model_dir),
            road_metadata
        )
    else:
        # Fallback to basic generation
        from .sdf_generator import generate_sdf_world
        generate_sdf_world(osm_file_path, output_path, world_name)
        return
    
    # Write to file
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sdf_xml)
    
    print(f"✅ Enhanced SDF world generated: {output_path}")
    print(f"   Model: {model_name}")
    print(f"   World: {world_name}")
    if road_metadata:
        print(f"   Roads metadata: {len(road_metadata.get('roads', []))} roads")

