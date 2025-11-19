#!/usr/bin/env python3
"""
Spawn the saye robot on a specific street in Gazebo.
Creates an SDF file with the city model and the robot positioned on the requested street.
"""

import sys
import yaml
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom


def create_robot_spawn_sdf(spawn_file: str, street_name: str, output_file: str, 
                           model_name: str = "bari_3d", robot_model_path: str = None):
    """Create SDF with robot spawned on specific street."""
    
    # Load spawn points
    with open(spawn_file, 'r') as f:
        spawn_data = yaml.safe_load(f)
    
    spawn_points = spawn_data['spawn_points']
    
    # Find spawn points on this street
    matching = []
    for sp in spawn_points:
        road_name = sp.get('road_name', '')
        if street_name.lower() in road_name.lower() or road_name.lower() in street_name.lower():
            matching.append(sp)
    
    if not matching:
        print(f"❌ No spawn points found for street: {street_name}")
        print("\nAvailable streets:")
        streets = set()
        for sp in spawn_points:
            name = sp.get('road_name', 'Unnamed')
            if name:
                streets.add(name)
        for street in sorted(streets)[:20]:
            print(f"  - {street}")
        if len(streets) > 20:
            print(f"  ... and {len(streets) - 20} more")
        return 1
    
    # Use spawn point closest to TRUE map center (not 0,0 but actual center of map)
    import math
    
    # Calculate true map center from all spawn points
    all_east = [sp['position']['east'] for sp in spawn_points]
    all_north = [sp['position']['north'] for sp in spawn_points]
    true_center_east = (min(all_east) + max(all_east)) / 2
    true_center_north = (min(all_north) + max(all_north)) / 2
    
    closest_to_center = None
    min_dist_to_center = float('inf')
    for sp in matching:
        pos = sp['position']
        # Distance from TRUE map center (not 0,0)
        dist = math.sqrt((pos['east'] - true_center_east)**2 + (pos['north'] - true_center_north)**2)
        if dist < min_dist_to_center:
            min_dist_to_center = dist
            closest_to_center = sp
    
    spawn_point = closest_to_center
    pos = spawn_point['position']
    orient = spawn_point.get('orientation', {})
    yaw = orient.get('yaw', 0.0)
    
    print(f"✅ Found spawn point on: {spawn_point.get('road_name', street_name)}")
    print(f"   Position: ({pos['east']:.3f}, {pos['north']:.3f}, {pos['up']:.3f})")
    print(f"   Yaw: {yaw:.3f} rad ({yaw * 180 / 3.14159:.1f} deg)")
    print(f"   Creating SDF with robot...")
    
    # Determine robot model path
    if robot_model_path is None:
        script_dir = Path(__file__).parent.parent
        robot_model_path = script_dir / "saye_description" / "models" / "saye" / "model.sdf"
        if not robot_model_path.exists():
            # Try alternative path
            robot_model_path = Path("/workspace/osm_city_pipeline/saye_description/models/saye/model.sdf")
    
    # Create SDF
    sdf = ET.Element('sdf', version='1.11')
    world = ET.SubElement(sdf, 'world', name='robot_spawn_test')
    
    # Add physics
    physics = ET.SubElement(world, 'physics')
    physics.set('type', 'ode')
    physics.set('name', 'default')
    max_step_size = ET.SubElement(physics, 'max_step_size')
    max_step_size.text = '0.001'
    real_time_factor = ET.SubElement(physics, 'real_time_factor')
    real_time_factor.text = '1.0'
    gravity_elem = ET.SubElement(physics, 'gravity')
    gravity_elem.text = '0 0 -9.81'
    
    # Add plugins
    plugin_physics = ET.SubElement(world, 'plugin')
    plugin_physics.set('filename', 'gz-sim-physics-system')
    plugin_physics.set('name', 'gz::sim::systems::Physics')
    
    plugin_sensors = ET.SubElement(world, 'plugin')
    plugin_sensors.set('filename', 'gz-sim-sensors-system')
    plugin_sensors.set('name', 'gz::sim::systems::Sensors')
    render_engine = ET.SubElement(plugin_sensors, 'render_engine')
    render_engine.text = 'ogre2'  # Use OGRE2 instead of vulkan (more compatible)
    
    plugin_scene = ET.SubElement(world, 'plugin')
    plugin_scene.set('filename', 'gz-sim-scene-broadcaster-system')
    plugin_scene.set('name', 'gz::sim::systems::SceneBroadcaster')
    
    plugin_user = ET.SubElement(world, 'plugin')
    plugin_user.set('filename', 'gz-sim-user-commands-system')
    plugin_user.set('name', 'gz::sim::systems::UserCommands')
    
    plugin_imu = ET.SubElement(world, 'plugin')
    plugin_imu.set('filename', 'gz-sim-imu-system')
    plugin_imu.set('name', 'gz::sim::systems::Imu')
    
    # Include the city model
    include_city = ET.SubElement(world, 'include')
    name_city = ET.SubElement(include_city, 'name')
    name_city.text = model_name
    uri_city = ET.SubElement(include_city, 'uri')
    uri_city.text = f'model://{model_name}'
    pose_city = ET.SubElement(include_city, 'pose')
    pose_city.text = '0 0 0 1.5708 0 0'
    
    # Include the robot model - use file:// URI for reliability
    include_robot = ET.SubElement(world, 'include')
    name_robot = ET.SubElement(include_robot, 'name')
    name_robot.text = 'saye'
    uri_robot = ET.SubElement(include_robot, 'uri')
    # Use absolute file path - most reliable
    script_dir = Path(__file__).parent.parent
    robot_model_path = script_dir / "saye_description" / "models" / "saye" / "model.sdf"
    if robot_model_path.exists():
        uri_robot.text = f'file://{robot_model_path.resolve()}'
    else:
        # Fallback to model:// URI
        uri_robot.text = 'model://saye'
    
    # Robot pose - positioned on the street
    pose_robot = ET.SubElement(include_robot, 'pose')
    # Position robot on the street (0.1m above ground for wheels to touch road)
    robot_z = pos['up'] + 0.1
    pose_robot.text = f"{pos['east']:.6f} {pos['north']:.6f} {robot_z:.6f} 0 0 {yaw:.6f}"
    
    # Add camera positioned ON THE STREET to view the robot
    gui = ET.SubElement(world, 'gui')
    gui.set('fullscreen', '0')
    
    # Default camera - positioned ON THE STREET, looking at the robot
    # This matches the user's request: camera should spawn on the street
    camera_default = ET.SubElement(gui, 'camera')
    camera_default.set('name', 'default')
    pose_cam = ET.SubElement(camera_default, 'pose')
    # Position camera ON THE STREET, behind the robot, looking at it
    # Calculate position behind robot based on yaw
    cam_offset_x = -5.0 * (1.0 if abs(yaw) < 1.57 else -1.0)  # Behind robot
    cam_offset_y = 0.0
    cam_x = pos['east'] + cam_offset_x * (1.0 if abs(yaw) < 1.57 else -1.0)
    cam_y = pos['north'] + cam_offset_y
    cam_z = 2.0  # Camera height on street (2m above ground)
    # Look at robot (pitch down slightly to see robot and street)
    pose_cam.text = f'{cam_x:.2f} {cam_y:.2f} {cam_z:.2f} 0 -0.3 {yaw:.2f}'
    view_controller = ET.SubElement(camera_default, 'view_controller')
    view_controller.text = 'orbit'
    
    # Follow camera (tracks robot)
    camera_follow = ET.SubElement(gui, 'camera')
    camera_follow.set('name', 'follow_camera')
    pose_cam_follow = ET.SubElement(camera_follow, 'pose')
    pose_cam_follow.text = '-8 0 4 0.4 0.6 0'
    view_controller_follow = ET.SubElement(camera_follow, 'view_controller')
    view_controller_follow.text = 'orbit'
    track_visual = ET.SubElement(camera_follow, 'track_visual')
    track_visual.text = 'saye::base_link::BaseVisual'
    
    # Format XML
    xml_str = ET.tostring(sdf, encoding='unicode')
    reparsed = minidom.parseString(xml_str)
    
    # Write to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(reparsed.toprettyxml(indent='  '))
    
    print(f"✅ SDF created: {output_file}")
    print(f"   Robot spawned on: {spawn_point.get('road_name', street_name)}")
    print(f"   Robot position: ({pos['east']:.3f}, {pos['north']:.3f}, {robot_z:.3f})")
    print(f"   Robot orientation: {yaw:.3f} rad ({yaw * 180 / 3.14159:.1f} deg)")
    print(f"\nTo visualize:")
    print(f"  source /opt/ros/jazzy/setup.bash")
    print(f"  export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models:$(pwd)/saye_description")
    print(f"  gz sim {output_file}")
    print(f"\nOr use the launch script:")
    print(f"  bash scripts/launch_gazebo.sh {output_file}")
    
    return 0


def main():
    if len(sys.argv) < 4:
        print("Usage: spawn_robot_on_street.py <spawn_file> <street_name> <output_sdf> [robot_model_path]")
        print("\nExample:")
        print("  python3 spawn_robot_on_street.py maps/bari_spawn_points.yaml 'Via Dante' worlds/robot_dante.sdf")
        return 1
    
    spawn_file = sys.argv[1]
    street_name = sys.argv[2]
    output_file = sys.argv[3]
    robot_model_path = sys.argv[4] if len(sys.argv) > 4 else None
    
    return create_robot_spawn_sdf(spawn_file, street_name, output_file, robot_model_path=robot_model_path)


if __name__ == "__main__":
    sys.exit(main())

