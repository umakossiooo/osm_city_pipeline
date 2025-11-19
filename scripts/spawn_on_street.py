#!/usr/bin/env python3
"""
Spawn a visible object on a specific street in Gazebo.
Creates an SDF file with the city model and a visible object on the requested street.
"""

import sys
import yaml
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom


def create_spawn_sdf(spawn_file: str, street_name: str, output_file: str, 
                     model_name: str = "bari_3d", object_type: str = "box"):
    """Create SDF with object spawned on specific street."""
    
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
    
    # Use first spawn point
    spawn_point = matching[0]
    pos = spawn_point['position']
    orient = spawn_point.get('orientation', {})
    yaw = orient.get('yaw', 0.0)
    
    print(f"✅ Found spawn point on: {spawn_point.get('road_name', street_name)}")
    print(f"   Position: ({pos['east']:.3f}, {pos['north']:.3f}, {pos['up']:.3f})")
    print(f"   Creating SDF with visible object...")
    
    # Create SDF
    sdf = ET.Element('sdf', version='1.11')
    world = ET.SubElement(sdf, 'world', name='spawn_test')
    
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
    
    # Include the city model
    include = ET.SubElement(world, 'include')
    name_elem = ET.SubElement(include, 'name')
    name_elem.text = model_name
    uri_elem = ET.SubElement(include, 'uri')
    uri_elem.text = f'model://{model_name}'
    pose_elem = ET.SubElement(include, 'pose')
    pose_elem.text = '0 0 0 1.5708 0 0'
    
    # Create visible object on the street
    if object_type == "box":
        # Create a colored box (robot-like)
        model = ET.SubElement(world, 'model', name='spawned_object')
        pose = ET.SubElement(model, 'pose')
        pose.text = f"{pos['east']:.6f} {pos['north']:.6f} {pos['up'] + 0.5:.6f} 0 0 {yaw:.6f}"
        
        link = ET.SubElement(model, 'link', name='link')
        
        # Visual - colored box
        visual = ET.SubElement(link, 'visual', name='visual')
        geometry = ET.SubElement(visual, 'geometry')
        box = ET.SubElement(geometry, 'box')
        size = ET.SubElement(box, 'size')
        size.text = '1.0 0.5 0.3'  # Length, width, height (like a small car)
        material = ET.SubElement(visual, 'material')
        ambient = ET.SubElement(material, 'ambient')
        ambient.text = '1.0 0.0 0.0 1'  # Bright red
        diffuse = ET.SubElement(material, 'diffuse')
        diffuse.text = '1.0 0.0 0.0 1'  # Bright red
        emissive = ET.SubElement(material, 'emissive')
        emissive.text = '0.3 0.0 0.0 1'  # Slight glow
        
        # Collision
        collision = ET.SubElement(link, 'collision', name='collision')
        geometry_coll = ET.SubElement(collision, 'geometry')
        box_coll = ET.SubElement(geometry_coll, 'box')
        size_coll = ET.SubElement(box_coll, 'size')
        size_coll.text = '1.0 0.5 0.3'
        
        # Add a sphere on top for visibility
        visual_sphere = ET.SubElement(link, 'visual', name='top_marker')
        pose_sphere = ET.SubElement(visual_sphere, 'pose')
        pose_sphere.text = '0 0 0.3 0 0 0'
        geometry_sphere = ET.SubElement(visual_sphere, 'geometry')
        sphere = ET.SubElement(geometry_sphere, 'sphere')
        radius = ET.SubElement(sphere, 'radius')
        radius.text = '0.2'
        material_sphere = ET.SubElement(visual_sphere, 'material')
        ambient_sphere = ET.SubElement(material_sphere, 'ambient')
        ambient_sphere.text = '1.0 1.0 0.0 1'  # Yellow
        diffuse_sphere = ET.SubElement(material_sphere, 'diffuse')
        diffuse_sphere.text = '1.0 1.0 0.0 1'  # Yellow
        
    elif object_type == "sphere":
        # Create a bright sphere
        model = ET.SubElement(world, 'model', name='spawned_object')
        pose = ET.SubElement(model, 'pose')
        pose.text = f"{pos['east']:.6f} {pos['north']:.6f} {pos['up'] + 1.0:.6f} 0 0 0"
        
        link = ET.SubElement(model, 'link', name='link')
        
        visual = ET.SubElement(link, 'visual', name='visual')
        geometry = ET.SubElement(visual, 'geometry')
        sphere = ET.SubElement(geometry, 'sphere')
        radius = ET.SubElement(sphere, 'radius')
        radius.text = '1.0'
        material = ET.SubElement(visual, 'material')
        ambient = ET.SubElement(material, 'ambient')
        ambient.text = '0.0 1.0 0.0 1'  # Bright green
        diffuse = ET.SubElement(material, 'diffuse')
        diffuse.text = '0.0 1.0 0.0 1'
        emissive = ET.SubElement(material, 'emissive')
        emissive.text = '0.2 0.5 0.2 1'
        
        collision = ET.SubElement(link, 'collision', name='collision')
        geometry_coll = ET.SubElement(collision, 'geometry')
        sphere_coll = ET.SubElement(geometry_coll, 'sphere')
        radius_coll = ET.SubElement(sphere_coll, 'radius')
        radius_coll.text = '1.0'
    
    # Add camera positioned to view the spawned object
    gui = ET.SubElement(world, 'gui')
    gui.set('fullscreen', '0')
    camera = ET.SubElement(gui, 'camera')
    camera.set('name', 'default')
    pose_cam = ET.SubElement(camera, 'pose')
    # Position camera above and behind the object
    cam_x = pos['east'] - 10 * (1 if yaw > -1.57 and yaw < 1.57 else -1)
    cam_y = pos['north'] - 10
    pose_cam.text = f'{cam_x:.2f} {cam_y:.2f} 15 0 -0.5 0'
    view_controller = ET.SubElement(camera, 'view_controller')
    view_controller.text = 'orbit'
    
    # Format XML
    xml_str = ET.tostring(sdf, encoding='unicode')
    reparsed = minidom.parseString(xml_str)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(reparsed.toprettyxml(indent='  '))
    
    print(f"✅ SDF created: {output_file}")
    print(f"   Object spawned on: {spawn_point.get('road_name', street_name)}")
    print(f"   Object type: {object_type}")
    print(f"   Position: ({pos['east']:.3f}, {pos['north']:.3f}, {pos['up'] + 0.5:.3f})")
    print(f"\nTo visualize:")
    print(f"  source /opt/ros/jazzy/setup.bash")
    print(f"  export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models")
    print(f"  gz sim {output_file}")
    print(f"\nOr use the launch script:")
    print(f"  bash scripts/launch_gazebo.sh {output_file}")
    
    return 0


def main():
    if len(sys.argv) < 4:
        print("Usage: spawn_on_street.py <spawn_file> <street_name> <output_sdf> [object_type]")
        print("\nObject types: 'box' (default) or 'sphere'")
        print("\nExample:")
        print("  python3 spawn_on_street.py maps/bari_spawn_points.yaml 'Via Dante' worlds/spawn_test.sdf")
        print("  python3 spawn_on_street.py maps/bari_spawn_points.yaml 'Via Dante' worlds/spawn_test.sdf sphere")
        return 1
    
    spawn_file = sys.argv[1]
    street_name = sys.argv[2]
    output_file = sys.argv[3]
    object_type = sys.argv[4] if len(sys.argv) > 4 else "box"
    
    if object_type not in ["box", "sphere"]:
        print(f"Error: object_type must be 'box' or 'sphere', got '{object_type}'")
        return 1
    
    return create_spawn_sdf(spawn_file, street_name, output_file, object_type=object_type)


if __name__ == "__main__":
    sys.exit(main())

