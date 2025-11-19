"""Generate Gazebo Harmonic SDF world files from geometry."""

from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET
from xml.dom import minidom
import math

from .geometry_builder import build_all_geometry
from .gis_projection import create_enu_from_osm


def create_sdf_world(geometries: Dict, world_name: str = "osm_city") -> str:
    """
    Create SDF world XML from geometry data.
    
    Args:
        geometries: Dictionary with roads, buildings, parks, sidewalks
        world_name: Name of the world
    
    Returns:
        SDF XML string
    """
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
    # Gravity is set as attribute in SDF 1.11
    gravity_elem = ET.SubElement(physics, 'gravity')
    gravity_elem.text = '0 0 -9.81'
    
    # Add scene
    scene = ET.SubElement(world, 'scene')
    ambient = ET.SubElement(scene, 'ambient')
    ambient.text = '0.4 0.4 0.4 1'
    background = ET.SubElement(scene, 'background')
    background.text = '0.7 0.7 0.7 1'
    shadows = ET.SubElement(scene, 'shadows')
    shadows.text = 'true'
    
    # Add ground plane
    ground_plane = ET.SubElement(world, 'model', name='ground_plane')
    static = ET.SubElement(ground_plane, 'static')
    static.text = 'true'
    link = ET.SubElement(ground_plane, 'link', name='link')
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
    material = ET.SubElement(visual, 'material')
    # Use lighter grey for ground plane to match reference image
    ambient = ET.SubElement(material, 'ambient')
    ambient.text = '0.85 0.85 0.85 1'  # Light grey/white
    diffuse = ET.SubElement(material, 'diffuse')
    diffuse.text = '0.9 0.9 0.9 1'  # Light grey/white
    specular = ET.SubElement(material, 'specular')
    specular.text = '0.5 0.5 0.5 1'
    
    # Add roads (grey drivable surfaces)
    for i, road in enumerate(geometries.get('roads', [])):
        road_model = ET.SubElement(world, 'model', name=f'road_{road["way_id"]}')
        static = ET.SubElement(road_model, 'static')
        static.text = 'true'
        link = ET.SubElement(road_model, 'link', name='link')
        
        # Create road mesh from vertices
        vertices = road['vertices']
        if len(vertices) >= 2:
            # Create a simple road segment
            for j in range(len(vertices) - 1):
                v1 = vertices[j]
                v2 = vertices[j + 1]
                
                # Calculate road segment center and orientation
                center_x = (v1[0] + v2[0]) / 2.0
                center_y = (v1[1] + v2[1]) / 2.0
                center_z = (v1[2] + v2[2]) / 2.0
                
                # Calculate length and angle
                dx = v2[0] - v1[0]
                dy = v2[1] - v1[1]
                length = math.sqrt(dx*dx + dy*dy)
                angle = math.atan2(dy, dx)
                
                if length > 0.1:  # Only create if segment is meaningful
                    # Create visual
                    visual = ET.SubElement(link, 'visual', name=f'visual_{j}')
                    pose_vis = ET.SubElement(visual, 'pose')
                    pose_vis.text = f'{center_x} {center_y} {center_z} 0 0 {angle}'
                    geometry_vis = ET.SubElement(visual, 'geometry')
                    box_vis = ET.SubElement(geometry_vis, 'box')
                    size_vis = ET.SubElement(box_vis, 'size')
                    size_vis.text = f'{length} {road["width"]} 0.1'
                    material_vis = ET.SubElement(visual, 'material')
                    # Use dark grey/black for roads to distinguish from ground
                    ambient = ET.SubElement(material_vis, 'ambient')
                    ambient.text = '0.15 0.15 0.15 1'  # Dark grey
                    diffuse = ET.SubElement(material_vis, 'diffuse')
                    diffuse.text = '0.2 0.2 0.2 1'  # Dark grey
                    specular = ET.SubElement(material_vis, 'specular')
                    specular.text = '0.1 0.1 0.1 1'
                    
                    # Create collision
                    collision = ET.SubElement(link, 'collision', name=f'collision_{j}')
                    pose_coll = ET.SubElement(collision, 'pose')
                    pose_coll.text = f'{center_x} {center_y} {center_z} 0 0 {angle}'
                    geometry_coll = ET.SubElement(collision, 'geometry')
                    box_coll = ET.SubElement(geometry_coll, 'box')
                    size_coll = ET.SubElement(box_coll, 'size')
                    size_coll.text = f'{length} {road["width"]} 0.1'
    
    # Add buildings (extruded)
    for i, building in enumerate(geometries.get('buildings', [])):
        building_model = ET.SubElement(world, 'model', name=f'building_{building.get("way_id", i)}')
        static = ET.SubElement(building_model, 'static')
        static.text = 'true'
        link = ET.SubElement(building_model, 'link', name='link')
        
        base_vertices = building['base_vertices']
        if len(base_vertices) >= 3:
            # Calculate building center
            center_x = sum(v[0] for v in base_vertices) / len(base_vertices)
            center_y = sum(v[1] for v in base_vertices) / len(base_vertices)
            center_z = building['height'] / 2.0
            
            # Create building as a box (simplified - could use mesh for complex shapes)
            # For now, use bounding box
            min_x = min(v[0] for v in base_vertices)
            max_x = max(v[0] for v in base_vertices)
            min_y = min(v[1] for v in base_vertices)
            max_y = max(v[1] for v in base_vertices)
            
            width = max_x - min_x
            depth = max_y - min_y
            height = building['height']
            
            # Lower threshold to include smaller buildings
            if width > 0.05 and depth > 0.05:
                # Create building with separate roof and walls like in the reference image
                # Roof (dark red) - positioned at top
                roof_visual = ET.SubElement(link, 'visual', name='roof')
                roof_pose = ET.SubElement(roof_visual, 'pose')
                roof_z = height  # Roof at top of building
                roof_pose.text = f'{center_x} {center_y} {roof_z} 0 0 0'
                roof_geometry = ET.SubElement(roof_visual, 'geometry')
                roof_box = ET.SubElement(roof_geometry, 'box')
                roof_size = ET.SubElement(roof_box, 'size')
                roof_size.text = f'{width} {depth} 0.1'  # Thin roof layer
                roof_material = ET.SubElement(roof_visual, 'material')
                roof_ambient = ET.SubElement(roof_material, 'ambient')
                roof_ambient.text = '0.4 0.1 0.1 1'  # Dark red
                roof_diffuse = ET.SubElement(roof_material, 'diffuse')
                roof_diffuse.text = '0.5 0.15 0.15 1'  # Dark red
                roof_specular = ET.SubElement(roof_material, 'specular')
                roof_specular.text = '0.2 0.1 0.1 1'
                
                # Walls (light grey) - four sides
                wall_height = height
                wall_thickness = 0.1
                
                # Front wall (positive Y)
                front_wall = ET.SubElement(link, 'visual', name='front_wall')
                front_pose = ET.SubElement(front_wall, 'pose')
                front_pose.text = f'{center_x} {center_y + depth/2} {wall_height/2} 0 0 0'
                front_geometry = ET.SubElement(front_wall, 'geometry')
                front_box = ET.SubElement(front_geometry, 'box')
                front_size = ET.SubElement(front_box, 'size')
                front_size.text = f'{width} {wall_thickness} {wall_height}'
                front_material = ET.SubElement(front_wall, 'material')
                front_ambient = ET.SubElement(front_material, 'ambient')
                front_ambient.text = '0.7 0.7 0.7 1'  # Light grey
                front_diffuse = ET.SubElement(front_material, 'diffuse')
                front_diffuse.text = '0.8 0.8 0.8 1'  # Light grey
                
                # Back wall (negative Y)
                back_wall = ET.SubElement(link, 'visual', name='back_wall')
                back_pose = ET.SubElement(back_wall, 'pose')
                back_pose.text = f'{center_x} {center_y - depth/2} {wall_height/2} 0 0 0'
                back_geometry = ET.SubElement(back_wall, 'geometry')
                back_box = ET.SubElement(back_geometry, 'box')
                back_size = ET.SubElement(back_box, 'size')
                back_size.text = f'{width} {wall_thickness} {wall_height}'
                back_material = ET.SubElement(back_wall, 'material')
                back_ambient = ET.SubElement(back_material, 'ambient')
                back_ambient.text = '0.7 0.7 0.7 1'
                back_diffuse = ET.SubElement(back_material, 'diffuse')
                back_diffuse.text = '0.8 0.8 0.8 1'
                
                # Left wall (negative X)
                left_wall = ET.SubElement(link, 'visual', name='left_wall')
                left_pose = ET.SubElement(left_wall, 'pose')
                left_pose.text = f'{center_x - width/2} {center_y} {wall_height/2} 0 0 0'
                left_geometry = ET.SubElement(left_wall, 'geometry')
                left_box = ET.SubElement(left_geometry, 'box')
                left_size = ET.SubElement(left_box, 'size')
                left_size.text = f'{wall_thickness} {depth} {wall_height}'
                left_material = ET.SubElement(left_wall, 'material')
                left_ambient = ET.SubElement(left_material, 'ambient')
                left_ambient.text = '0.7 0.7 0.7 1'
                left_diffuse = ET.SubElement(left_material, 'diffuse')
                left_diffuse.text = '0.8 0.8 0.8 1'
                
                # Right wall (positive X)
                right_wall = ET.SubElement(link, 'visual', name='right_wall')
                right_pose = ET.SubElement(right_wall, 'pose')
                right_pose.text = f'{center_x + width/2} {center_y} {wall_height/2} 0 0 0'
                right_geometry = ET.SubElement(right_wall, 'geometry')
                right_box = ET.SubElement(right_geometry, 'box')
                right_size = ET.SubElement(right_box, 'size')
                right_size.text = f'{wall_thickness} {depth} {wall_height}'
                right_material = ET.SubElement(right_wall, 'material')
                right_ambient = ET.SubElement(right_material, 'ambient')
                right_ambient.text = '0.7 0.7 0.7 1'
                right_diffuse = ET.SubElement(right_material, 'diffuse')
                right_diffuse.text = '0.8 0.8 0.8 1'
                
                # Collision
                collision = ET.SubElement(link, 'collision', name='collision')
                pose_coll = ET.SubElement(collision, 'pose')
                pose_coll.text = f'{center_x} {center_y} {center_z} 0 0 0'
                geometry_coll = ET.SubElement(collision, 'geometry')
                box_coll = ET.SubElement(geometry_coll, 'box')
                size_coll = ET.SubElement(box_coll, 'size')
                size_coll.text = f'{width} {depth} {height}'
    
    # Add parks (green areas)
    for i, park in enumerate(geometries.get('parks', [])):
        park_model = ET.SubElement(world, 'model', name=f'park_{park.get("way_id", i)}')
        static = ET.SubElement(park_model, 'static')
        static.text = 'true'
        link = ET.SubElement(park_model, 'link', name='link')
        
        vertices = park['vertices']
        if len(vertices) >= 3:
            # Calculate park center and bounding box
            center_x = sum(v[0] for v in vertices) / len(vertices)
            center_y = sum(v[1] for v in vertices) / len(vertices)
            center_z = 0.05  # Slightly above ground
            
            min_x = min(v[0] for v in vertices)
            max_x = max(v[0] for v in vertices)
            min_y = min(v[1] for v in vertices)
            max_y = max(v[1] for v in vertices)
            
            width = max_x - min_x
            depth = max_y - min_y
            
            if width > 0.1 and depth > 0.1:
                # Visual
                visual = ET.SubElement(link, 'visual', name='visual')
                pose_vis = ET.SubElement(visual, 'pose')
                pose_vis.text = f'{center_x} {center_y} {center_z} 0 0 0'
                geometry_vis = ET.SubElement(visual, 'geometry')
                box_vis = ET.SubElement(geometry_vis, 'box')
                size_vis = ET.SubElement(box_vis, 'size')
                size_vis.text = f'{width} {depth} 0.1'
                material_vis = ET.SubElement(visual, 'material')
                # Use vibrant green for parks/trees
                ambient = ET.SubElement(material_vis, 'ambient')
                ambient.text = '0.1 0.4 0.1 1'  # Dark green
                diffuse = ET.SubElement(material_vis, 'diffuse')
                diffuse.text = '0.2 0.7 0.2 1'  # Bright green
                specular = ET.SubElement(material_vis, 'specular')
                specular.text = '0.1 0.3 0.1 1'
    
    # Add sidewalks (green strips between roads and buildings)
    for i, sidewalk in enumerate(geometries.get('sidewalks', [])):
        sidewalk_model = ET.SubElement(world, 'model', name=f'sidewalk_{sidewalk["way_id"]}')
        static = ET.SubElement(sidewalk_model, 'static')
        static.text = 'true'
        link = ET.SubElement(sidewalk_model, 'link', name='link')
        
        vertices = sidewalk['vertices']
        if len(vertices) >= 2:
            # Create sidewalk segments similar to roads
            for j in range(len(vertices) - 1):
                v1 = vertices[j]
                v2 = vertices[j + 1]
                
                center_x = (v1[0] + v2[0]) / 2.0
                center_y = (v1[1] + v2[1]) / 2.0
                center_z = 0.02  # Slightly above ground
                
                dx = v2[0] - v1[0]
                dy = v2[1] - v1[1]
                length = math.sqrt(dx*dx + dy*dy)
                angle = math.atan2(dy, dx)
                
                if length > 0.1:
                    # Create visual
                    visual = ET.SubElement(link, 'visual', name=f'visual_{j}')
                    pose_vis = ET.SubElement(visual, 'pose')
                    pose_vis.text = f'{center_x} {center_y} {center_z} 0 0 {angle}'
                    geometry_vis = ET.SubElement(visual, 'geometry')
                    box_vis = ET.SubElement(geometry_vis, 'box')
                    size_vis = ET.SubElement(box_vis, 'size')
                    size_vis.text = f'{length} {sidewalk["width"]} 0.05'
                    material_vis = ET.SubElement(visual, 'material')
                    # Use green for sidewalks (like in reference image)
                    ambient = ET.SubElement(material_vis, 'ambient')
                    ambient.text = '0.15 0.4 0.15 1'  # Dark green
                    diffuse = ET.SubElement(material_vis, 'diffuse')
                    diffuse.text = '0.2 0.5 0.2 1'  # Medium green
                    specular = ET.SubElement(material_vis, 'specular')
                    specular.text = '0.1 0.2 0.1 1'
    
    # Add default camera pose
    gui = ET.SubElement(world, 'gui')
    camera = ET.SubElement(gui, 'camera', name='user_camera')
    pose_cam = ET.SubElement(camera, 'pose')
    # Position camera above the center, looking down
    pose_cam.text = '0 0 50 0 1.57 0'  # x, y, z, roll, pitch, yaw
    # View controller removed - not needed for SDF 1.11
    
    # Convert to string
    rough_string = ET.tostring(sdf, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='  ')


def generate_sdf_world(osm_file_path: str, output_path: str, world_name: str = "osm_city") -> None:
    """
    Generate SDF world file from OSM file.
    
    Args:
        osm_file_path: Path to OSM file
        output_path: Path to output SDF file
        world_name: Name of the world
    """
    # Create ENU projection
    enu_proj = create_enu_from_osm(osm_file_path)
    
    # Build all geometry
    geometries = build_all_geometry(osm_file_path, enu_proj)
    
    # Generate SDF
    sdf_xml = create_sdf_world(geometries, world_name)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sdf_xml)

