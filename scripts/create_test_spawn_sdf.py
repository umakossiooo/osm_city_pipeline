#!/usr/bin/env python3
"""
Create a test SDF file with markers on multiple different streets.
This demonstrates that we can spawn on different streets.
"""

import sys
import yaml
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom


def create_test_spawn_sdf(spawn_file: str, roads_file: str, output_file: str, 
                          street_names: list = None):
    """Create SDF with markers on multiple streets."""
    
    # Load spawn points
    with open(spawn_file, 'r') as f:
        spawn_data = yaml.safe_load(f)
    
    spawn_points = spawn_data['spawn_points']
    
    # Load roads for street names
    with open(roads_file, 'r') as f:
        roads_data = json.load(f)
    
    # Default streets to test
    if street_names is None:
        street_names = [
            "Via Dante Alighieri",
            "Via Alessandro Maria Calefati",
            "Via Nicolò Putignani",
            "Piazza Umberto Primo",
            "Via Michele Garruba"
        ]
    
    # Find spawn points for each street
    street_spawns = {}
    for street_name in street_names:
        matching = []
        for sp in spawn_points:
            road_name = sp.get('road_name', '')
            if street_name.lower() in road_name.lower() or road_name.lower() in street_name.lower():
                matching.append(sp)
        if matching:
            street_spawns[street_name] = matching[0]  # Use first spawn point
    
    # Create SDF
    sdf = ET.Element('sdf', version='1.11')
    world = ET.SubElement(sdf, 'world', name='test_multi_street_spawn')
    
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
    render_engine.text = 'vulkan'
    
    plugin_scene = ET.SubElement(world, 'plugin')
    plugin_scene.set('filename', 'gz-sim-scene-broadcaster-system')
    plugin_scene.set('name', 'gz::sim::systems::SceneBroadcaster')
    
    # Include the city model
    include = ET.SubElement(world, 'include')
    name_elem = ET.SubElement(include, 'name')
    name_elem.text = 'bari_3d'
    uri_elem = ET.SubElement(include, 'uri')
    uri_elem.text = 'model://bari_3d'
    pose_elem = ET.SubElement(include, 'pose')
    pose_elem.text = '0 0 0 1.5708 0 0'
    
    # Add markers for each street (different colors)
    colors = [
        (1.0, 0.0, 0.0),  # Red
        (0.0, 1.0, 0.0),  # Green
        (0.0, 0.0, 1.0),  # Blue
        (1.0, 1.0, 0.0),  # Yellow
        (1.0, 0.0, 1.0),  # Magenta
    ]
    
    for i, (street_name, spawn_point) in enumerate(street_spawns.items()):
        pos = spawn_point['position']
        orient = spawn_point.get('orientation', {})
        yaw = orient.get('yaw', 0.0)
        color = colors[i % len(colors)]
        
        # Create a visible marker (sphere) on this street
        model = ET.SubElement(world, 'model', name=f'marker_street_{i}')
        static = ET.SubElement(model, 'static')
        static.text = 'true'
        link = ET.SubElement(model, 'link', name='link')
        
        # Pose
        pose = ET.SubElement(model, 'pose')
        pose.text = f"{pos['east']:.6f} {pos['north']:.6f} {pos['up'] + 2.0:.6f} 0 0 {yaw:.6f}"
        
        # Visual - large sphere
        visual = ET.SubElement(link, 'visual', name='visual')
        geometry = ET.SubElement(visual, 'geometry')
        sphere = ET.SubElement(geometry, 'sphere')
        radius = ET.SubElement(sphere, 'radius')
        radius.text = '2.0'
        material = ET.SubElement(visual, 'material')
        ambient = ET.SubElement(material, 'ambient')
        ambient.text = f'{color[0]} {color[1]} {color[2]} 1'
        diffuse = ET.SubElement(material, 'diffuse')
        diffuse.text = f'{color[0]} {color[1]} {color[2]} 1'
        
        # Collision
        collision = ET.SubElement(link, 'collision', name='collision')
        geometry_coll = ET.SubElement(collision, 'geometry')
        sphere_coll = ET.SubElement(geometry_coll, 'sphere')
        radius_coll = ET.SubElement(sphere_coll, 'radius')
        radius_coll.text = '2.0'
        
        # Add text label (using a box with name)
        print(f"  Street {i+1}: {street_name}")
        print(f"    Position: ({pos['east']:.3f}, {pos['north']:.3f}, {pos['up']:.3f})")
        print(f"    Color: RGB{color}")
        print()
    
    # Add camera
    gui = ET.SubElement(world, 'gui')
    gui.set('fullscreen', '0')
    camera = ET.SubElement(gui, 'camera')
    camera.set('name', 'default')
    pose_cam = ET.SubElement(camera, 'pose')
    pose_cam.text = '0 0 100 0 -1.57 0'
    view_controller = ET.SubElement(camera, 'view_controller')
    view_controller.text = 'orbit'
    
    # Format XML
    xml_str = ET.tostring(sdf, encoding='unicode')
    reparsed = minidom.parseString(xml_str)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(reparsed.toprettyxml(indent='  '))
    
    print(f"✅ Test SDF created: {output_file}")
    print(f"   {len(street_spawns)} markers placed on different streets")
    print(f"   Each marker is a different color and positioned on its street")
    print(f"   Launch with: gz sim {output_file}")
    
    return 0


def main():
    if len(sys.argv) < 4:
        print("Usage: create_test_spawn_sdf.py <spawn_file> <roads_file> <output_sdf>")
        print("\nExample:")
        print("  python3 create_test_spawn_sdf.py maps/bari_spawn_points.yaml maps/bari_roads.json worlds/test_multi_street.sdf")
        return 1
    
    spawn_file = sys.argv[1]
    roads_file = sys.argv[2]
    output_file = sys.argv[3]
    
    return create_test_spawn_sdf(spawn_file, roads_file, output_file)


if __name__ == "__main__":
    sys.exit(main())

