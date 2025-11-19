#!/usr/bin/env python3
"""OSM → Procedural city pipeline for Gazebo Harmonic + ROS 2 Jazzy."""
import argparse
import json
import math
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import xml.etree.ElementTree as ET

from pyproj import Transformer
from shapely.geometry import Polygon


MIN_SEGMENT_LENGTH = 50.0  # meters
MAX_SEGMENT_LENGTH = 100.0
DEFAULT_ROAD_WIDTH = 7.0
SIDEWALK_WIDTH = 1.5
SIDEWALK_HEIGHT = 0.12
ROAD_HEIGHT = 0.12
TREE_TRUNK_HEIGHT = 3.0
TREE_CROWN_RADIUS = 1.5
TREE_TRUNK_RADIUS = 0.18
DEFAULT_BUILDING_HEIGHT = 12.0
LEVEL_HEIGHT = 3.2


@dataclass
class Way:
    way_id: int
    node_refs: List[int]
    tags: Dict[str, str]


@dataclass
class Segment:
    seg_id: str
    start: Tuple[float, float]
    end: Tuple[float, float]
    width: float
    height: float
    parent_way: int


@dataclass
class SidewalkStrip:
    strip_id: str
    center: Tuple[float, float]
    length: float
    yaw: float
    width: float = SIDEWALK_WIDTH
    height: float = SIDEWALK_HEIGHT


@dataclass
class Building:
    name: str
    footprint: List[Tuple[float, float]]
    height: float
    centroid: Tuple[float, float]


@dataclass
class Tree:
    name: str
    position: Tuple[float, float]


class CoordinateFrame:
    def __init__(self, origin_lat: float, origin_lon: float, epsg: int, zone_label: str):
        self.origin_lat = origin_lat
        self.origin_lon = origin_lon
        self.utm_epsg = epsg
        self.utm_zone_label = zone_label
        self.transformer = Transformer.from_crs("epsg:4326", f"epsg:{epsg}", always_xy=True)
        origin_x, origin_y = self.latlon_to_utm(origin_lat, origin_lon)
        self.offset_x = -origin_x
        self.offset_y = -origin_y
        self.offset_yaw = 0.0

    @staticmethod
    def from_nodes(nodes: Dict[int, Tuple[float, float]]) -> "CoordinateFrame":
        if not nodes:
            raise RuntimeError("OSM file does not contain any nodes")
        sample_lat = float(sum(lat for lat, _ in nodes.values()) / len(nodes))
        sample_lon = float(sum(lon for _, lon in nodes.values()) / len(nodes))
        epsg, label = CoordinateFrame._utm_from_latlon(sample_lat, sample_lon)
        return CoordinateFrame(sample_lat, sample_lon, epsg, label)

    @staticmethod
    def _utm_from_latlon(lat: float, lon: float) -> Tuple[int, str]:
        zone = int((lon + 180.0) / 6.0) + 1
        is_northern = lat >= 0
        epsg = (32600 if is_northern else 32700) + zone
        zone_label = f"{zone}{'N' if is_northern else 'S'}"
        return epsg, zone_label

    def latlon_to_utm(self, lat: float, lon: float) -> Tuple[float, float]:
        x, y = self.transformer.transform(lon, lat)
        return float(x), float(y)

    def latlon_to_gazebo(self, lat: float, lon: float) -> Tuple[float, float]:
        x, y = self.latlon_to_utm(lat, lon)
        return x + self.offset_x, y + self.offset_y

    def utm_to_gazebo(self, x: float, y: float) -> Tuple[float, float]:
        return x + self.offset_x, y + self.offset_y

    def config_dict(self) -> Dict[str, object]:
        return {
            "origin_lat": round(self.origin_lat, 9),
            "origin_lon": round(self.origin_lon, 9),
            "utm_zone": self.utm_zone_label,
            "gazebo_offset": {"x": self.offset_x, "y": self.offset_y, "yaw": self.offset_yaw},
        }


class CityBuilder:
    def __init__(self, osm_file: Path, output_root: Path):
        self.osm_file = osm_file
        self.output_root = output_root
        self.config_dir = output_root / "config"
        self.world_dir = output_root / "world"
        self.models_dir = self.world_dir / "models"
        self.spawn_file = output_root / "spawn_points.json"
        self.camera_file = output_root / "camera_views.json"
        self.nodes: Dict[int, Tuple[float, float]] = {}
        self.ways: List[Way] = []
        self.node_tags: Dict[int, Dict[str, str]] = {}
        self.node_usage: Dict[int, int] = {}
        self.frame: Optional[CoordinateFrame] = None
        self.gazebo_nodes: Dict[int, Tuple[float, float]] = {}
        self.model_includes: List[str] = []

    def run(self) -> None:
        self._parse_osm()
        self.frame = CoordinateFrame.from_nodes(self.nodes)
        self.gazebo_nodes = {
            node_id: self.frame.latlon_to_gazebo(lat, lon)
            for node_id, (lat, lon) in self.nodes.items()
        }
        self._prepare_directories()
        self._write_map_config()
        segments = self._build_road_segments()
        sidewalks = self._build_sidewalks(segments)
        buildings = self._build_buildings()
        trees = self._build_trees()
        self._write_ground_plane()
        self._write_road_models(segments)
        self._write_sidewalk_models(sidewalks)
        self._write_building_models(buildings)
        self._write_tree_models(trees)
        self._write_world_file()
        self._write_spawn_points(segments)
        self._write_camera_views(segments, buildings, trees)
        print(
            f"Generated {len(segments)} road segments, {len(sidewalks)} sidewalks, "
            f"{len(buildings)} buildings, {len(trees)} trees."
        )

    def _parse_osm(self) -> None:
        tree = ET.parse(self.osm_file)
        root = tree.getroot()
        for node in root.findall("node"):
            node_id = int(node.attrib["id"])
            lat = float(node.attrib["lat"])
            lon = float(node.attrib["lon"])
            self.nodes[node_id] = (lat, lon)
            self.node_usage[node_id] = 0
            tags = {tag.attrib["k"]: tag.attrib["v"] for tag in node.findall("tag")}
            if tags:
                self.node_tags[node_id] = tags
        for way_elem in root.findall("way"):
            node_refs = [int(nd.attrib["ref"]) for nd in way_elem.findall("nd") if nd.attrib.get("ref")]
            tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way_elem.findall("tag")}
            if not node_refs:
                continue
            for ref in node_refs:
                if ref in self.node_usage:
                    self.node_usage[ref] += 1
            self.ways.append(Way(int(way_elem.attrib["id"]), node_refs, tags))

    def _prepare_directories(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.world_dir.mkdir(parents=True, exist_ok=True)
        if self.models_dir.exists():
            shutil.rmtree(self.models_dir)
        (self.models_dir / "roads").mkdir(parents=True, exist_ok=True)
        (self.models_dir / "sidewalks").mkdir(parents=True, exist_ok=True)
        (self.models_dir / "buildings").mkdir(parents=True, exist_ok=True)
        (self.models_dir / "vegetation" / "trees").mkdir(parents=True, exist_ok=True)
        (self.models_dir / "common").mkdir(parents=True, exist_ok=True)

    def _write_map_config(self) -> None:
        import yaml  # lazy import to keep global deps minimal

        cfg_path = self.config_dir / "map_config.yaml"
        cfg_path.write_text(yaml.safe_dump(self.frame.config_dict(), sort_keys=False), encoding="utf-8")

    def _nodes_to_coords(self, refs: Sequence[int]) -> List[Tuple[float, float]]:
        coords = []
        for ref in refs:
            if ref in self.gazebo_nodes:
                coords.append(self.gazebo_nodes[ref])
        return coords

    def _build_road_segments(self) -> List[Segment]:
        segments: List[Segment] = []
        seg_index = 0
        for way in self.ways:
            if "highway" not in way.tags:
                continue
            coords = self._nodes_to_coords(way.node_refs)
            if len(coords) < 2:
                continue
            width = self._road_width(way.tags)
            sliced = self._slice_polyline(coords)
            for part in sliced:
                start, end = part
                length = math.dist(start, end)
                if length < 1.0:
                    continue
                seg_index += 1
                seg_id = f"segment_{seg_index:05d}"
                segments.append(
                    Segment(seg_id=seg_id, start=start, end=end, width=width, height=ROAD_HEIGHT, parent_way=way.way_id)
                )
        return segments

    def _slice_polyline(self, points: Sequence[Tuple[float, float]]) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        if len(points) < 2:
            return []
        cumulative = [0.0]
        for idx in range(1, len(points)):
            cumulative.append(cumulative[-1] + math.dist(points[idx - 1], points[idx]))
        total_length = cumulative[-1]
        if total_length < MIN_SEGMENT_LENGTH:
            return [(points[0], points[-1])]
        segment_count = max(1, math.ceil(total_length / MAX_SEGMENT_LENGTH))
        while segment_count > 1 and total_length / segment_count < MIN_SEGMENT_LENGTH:
            segment_count -= 1
        step = total_length / segment_count

        def point_at(distance: float) -> Tuple[float, float]:
            if distance <= 0:
                return points[0]
            if distance >= total_length:
                return points[-1]
            for idx in range(1, len(points)):
                if distance <= cumulative[idx]:
                    seg_len = cumulative[idx] - cumulative[idx - 1]
                    if seg_len == 0:
                        continue
                    ratio = (distance - cumulative[idx - 1]) / seg_len
                    x0, y0 = points[idx - 1]
                    x1, y1 = points[idx]
                    return (x0 + ratio * (x1 - x0), y0 + ratio * (y1 - y0))
            return points[-1]

        cut_distances = [step * i for i in range(segment_count)] + [total_length]
        segments = []
        for start_d, end_d in zip(cut_distances[:-1], cut_distances[1:]):
            if end_d - start_d < MIN_SEGMENT_LENGTH and segments:
                # merge short tail into previous by extending end point
                prev_start, _ = segments[-1]
                segments[-1] = (prev_start, point_at(end_d))
            else:
                segments.append((point_at(start_d), point_at(end_d)))
        return segments

    def _road_width(self, tags: Dict[str, str]) -> float:
        if "width" in tags:
            try:
                return max(3.0, float(tags["width"]))
            except ValueError:
                pass
        lanes = 1
        if "lanes" in tags:
            try:
                lanes = max(1, int(tags["lanes"]))
            except ValueError:
                pass
        return lanes * 3.5

    def _build_sidewalks(self, road_segments: Sequence[Segment]) -> List[SidewalkStrip]:
        strips: List[SidewalkStrip] = []
        strip_index = 0
        # Sidewalks derived from road attributes
        way_sidewalk_map = {way.way_id: way.tags.get("sidewalk", "") for way in self.ways if "highway" in way.tags}
        for segment in road_segments:
            side_opt = way_sidewalk_map.get(segment.parent_way, "")
            if side_opt not in {"left", "right", "both"}:
                continue
            dx = segment.end[0] - segment.start[0]
            dy = segment.end[1] - segment.start[1]
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            yaw = math.atan2(dy, dx)
            nx = -dy / length
            ny = dx / length
            base_mid = ((segment.start[0] + segment.end[0]) / 2.0, (segment.start[1] + segment.end[1]) / 2.0)
            offsets = []
            if side_opt in {"left", "both"}:
                offsets.append(1)
            if side_opt in {"right", "both"}:
                offsets.append(-1)
            for direction in offsets:
                strip_index += 1
                offset_dist = direction * (segment.width / 2.0 + SIDEWALK_WIDTH / 2.0)
                center = (base_mid[0] + nx * offset_dist, base_mid[1] + ny * offset_dist)
                strips.append(
                    SidewalkStrip(
                        strip_id=f"sidewalk_{strip_index:05d}",
                        center=center,
                        length=length,
                        yaw=yaw,
                    )
                )
        # Explicit sidewalk ways
        for way in self.ways:
            if way.tags.get("footway") != "sidewalk" and way.tags.get("highway") != "footway":
                continue
            coords = self._nodes_to_coords(way.node_refs)
            for start, end in zip(coords[:-1], coords[1:]):
                length = math.dist(start, end)
                if length < 1.0:
                    continue
                yaw = math.atan2(end[1] - start[1], end[0] - start[0])
                center = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
                strip_index += 1
                strips.append(
                    SidewalkStrip(
                        strip_id=f"sidewalk_{strip_index:05d}",
                        center=center,
                        length=length,
                        yaw=yaw,
                    )
                )
        return strips

    def _build_buildings(self) -> List[Building]:
        buildings: List[Building] = []
        for way in self.ways:
            if "building" not in way.tags:
                continue
            coords = self._nodes_to_coords(way.node_refs)
            if len(coords) < 3:
                continue
            polygon = Polygon(coords)
            if polygon.is_empty or polygon.area < 1.0:
                continue
            centroid = (polygon.centroid.x, polygon.centroid.y)
            height = self._building_height(way.tags)
            footprint = [(pt[0] - centroid[0], pt[1] - centroid[1]) for pt in polygon.exterior.coords]
            buildings.append(
                Building(
                    name=f"building_{way.way_id}",
                    footprint=footprint,
                    height=height,
                    centroid=centroid,
                )
            )
        return buildings

    def _building_height(self, tags: Dict[str, str]) -> float:
        if "height" in tags:
            try:
                val = float(tags["height"].replace("m", ""))
                if val > 2:
                    return val
            except ValueError:
                pass
        if "building:levels" in tags:
            try:
                levels = int(tags["building:levels"])
                return max(3.0, levels * LEVEL_HEIGHT)
            except ValueError:
                pass
        return DEFAULT_BUILDING_HEIGHT

    def _build_trees(self) -> List[Tree]:
        trees: List[Tree] = []
        for node_id, (lat, lon) in self.nodes.items():
            tags = self._node_tags(node_id)
            if tags.get("natural") != "tree":
                continue
            gx, gy = self.gazebo_nodes[node_id]
            trees.append(Tree(name=f"tree_{node_id}", position=(gx, gy)))
        return trees

    def _node_tags(self, node_id: int) -> Dict[str, str]:
        return self.node_tags.get(node_id, {})

    def _write_ground_plane(self) -> None:
        name = "ground_plane"
        model_dir = self.models_dir / "common" / name
        model_dir.mkdir(parents=True, exist_ok=True)
        size = 1000.0
        sdf = f"""
<sdf version='1.9'>
  <model name='{name}'>
    <static>true</static>
    <link name='link'>
      <collision name='collision'>
        <geometry>
          <plane>
            <normal>0 0 1</normal>
            <size>{size} {size}</size>
          </plane>
        </geometry>
        <surface>
          <friction>
            <ode>
              <mu>1.0</mu>
              <mu2>1.0</mu2>
            </ode>
          </friction>
        </surface>
      </collision>
      <visual name='visual'>
        <geometry>
          <plane>
            <normal>0 0 1</normal>
            <size>{size} {size}</size>
          </plane>
        </geometry>
        <material>
          <ambient>0.4 0.4 0.4 1</ambient>
          <diffuse>0.5 0.5 0.5 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>
"""
        self._write_model_files(model_dir, name, sdf, "Procedural ground plane")
        self.model_includes.append("models/common/ground_plane")

    def _write_road_models(self, segments: Sequence[Segment]) -> None:
        for segment in segments:
            model_dir = self.models_dir / "roads" / segment.seg_id
            model_dir.mkdir(parents=True, exist_ok=True)
            center_x = (segment.start[0] + segment.end[0]) / 2.0
            center_y = (segment.start[1] + segment.end[1]) / 2.0
            yaw = math.atan2(segment.end[1] - segment.start[1], segment.end[0] - segment.start[0])
            length = math.dist(segment.start, segment.end)
            sdf = self._box_model_sdf(
                name=segment.seg_id,
                pose=(center_x, center_y, segment.height / 2.0, 0.0, 0.0, yaw),
                size=(length, segment.width, segment.height),
                color=(0.05, 0.05, 0.05, 1.0),
            )
            self._write_model_files(model_dir, segment.seg_id, sdf, "Road segment")
            self.model_includes.append(f"models/roads/{segment.seg_id}")

    def _write_sidewalk_models(self, sidewalks: Sequence[SidewalkStrip]) -> None:
        for strip in sidewalks:
            model_dir = self.models_dir / "sidewalks" / strip.strip_id
            model_dir.mkdir(parents=True, exist_ok=True)
            sdf = self._box_model_sdf(
                name=strip.strip_id,
                pose=(strip.center[0], strip.center[1], strip.height / 2.0, 0.0, 0.0, strip.yaw),
                size=(strip.length, strip.width, strip.height),
                color=(0.7, 0.7, 0.7, 1.0),
            )
            self._write_model_files(model_dir, strip.strip_id, sdf, "Sidewalk strip")
            self.model_includes.append(f"models/sidewalks/{strip.strip_id}")

    def _write_building_models(self, buildings: Sequence[Building]) -> None:
        for building in buildings:
            model_dir = self.models_dir / "buildings" / building.name
            model_dir.mkdir(parents=True, exist_ok=True)
            poly_points = "\n".join(f"        <point>{x:.3f} {y:.3f}</point>" for x, y in building.footprint)
            sdf = f"""
<sdf version='1.9'>
  <model name='{building.name}'>
    <static>true</static>
    <pose>{building.centroid[0]:.3f} {building.centroid[1]:.3f} 0 0 0 0</pose>
    <link name='body'>
      <pose>0 0 {building.height/2:.3f} 0 0 0</pose>
      <collision name='collision'>
        <geometry>
          <polyline>
            <height>{building.height:.3f}</height>
{poly_points}
          </polyline>
        </geometry>
      </collision>
      <visual name='visual'>
        <geometry>
          <polyline>
            <height>{building.height:.3f}</height>
{poly_points}
          </polyline>
        </geometry>
        <material>
          <ambient>0.6 0.6 0.6 1</ambient>
          <diffuse>0.7 0.7 0.7 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>
"""
            self._write_model_files(model_dir, building.name, sdf, "Building volume")
            self.model_includes.append(f"models/buildings/{building.name}")

    def _write_tree_models(self, trees: Sequence[Tree]) -> None:
        for tree in trees:
            model_dir = self.models_dir / "vegetation" / "trees" / tree.name
            model_dir.mkdir(parents=True, exist_ok=True)
            sdf = f"""
<sdf version='1.9'>
  <model name='{tree.name}'>
    <static>true</static>
    <pose>{tree.position[0]:.3f} {tree.position[1]:.3f} 0 0 0 0</pose>
    <link name='tree'>
      <collision name='trunk_collision'>
        <pose>0 0 {TREE_TRUNK_HEIGHT/2:.3f} 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>{TREE_TRUNK_RADIUS:.3f}</radius>
            <length>{TREE_TRUNK_HEIGHT:.3f}</length>
          </cylinder>
        </geometry>
      </collision>
      <visual name='trunk'>
        <pose>0 0 {TREE_TRUNK_HEIGHT/2:.3f} 0 0 0</pose>
        <geometry>
          <cylinder>
            <radius>{TREE_TRUNK_RADIUS:.3f}</radius>
            <length>{TREE_TRUNK_HEIGHT:.3f}</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.4 0.2 0.1 1</ambient>
          <diffuse>0.4 0.2 0.1 1</diffuse>
        </material>
      </visual>
      <visual name='crown'>
        <pose>0 0 {TREE_TRUNK_HEIGHT + TREE_CROWN_RADIUS:.3f} 0 0 0</pose>
        <geometry>
          <sphere>
            <radius>{TREE_CROWN_RADIUS:.3f}</radius>
          </sphere>
        </geometry>
        <material>
          <ambient>0.1 0.4 0.1 1</ambient>
          <diffuse>0.1 0.5 0.1 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>
"""
            self._write_model_files(model_dir, tree.name, sdf, "Tree asset")
            self.model_includes.append(f"models/vegetation/trees/{tree.name}")

    def _box_model_sdf(
        self,
        name: str,
        pose: Tuple[float, float, float, float, float, float],
        size: Tuple[float, float, float],
        color: Tuple[float, float, float, float],
    ) -> str:
        px, py, pz, roll, pitch, yaw = pose
        sx, sy, sz = size
        r, g, b, a = color
        return f"""
<sdf version='1.9'>
  <model name='{name}'>
    <static>true</static>
    <pose>{px:.3f} {py:.3f} {pz:.3f} {roll:.3f} {pitch:.3f} {yaw:.3f}</pose>
    <link name='link'>
      <collision name='collision'>
        <geometry>
          <box>
            <size>{sx:.3f} {sy:.3f} {sz:.3f}</size>
          </box>
        </geometry>
      </collision>
      <visual name='visual'>
        <geometry>
          <box>
            <size>{sx:.3f} {sy:.3f} {sz:.3f}</size>
          </box>
        </geometry>
        <material>
          <ambient>{r:.3f} {g:.3f} {b:.3f} {a:.3f}</ambient>
          <diffuse>{r:.3f} {g:.3f} {b:.3f} {a:.3f}</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>
"""

    def _write_model_files(self, model_dir: Path, model_name: str, sdf: str, description: str) -> None:
        (model_dir / "model.sdf").write_text(sdf.strip() + "\n", encoding="utf-8")
        config = f"""
<?xml version='1.0'?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version='1.9'>model.sdf</sdf>
  <author>
    <name>osm_city_pipeline</name>
    <email>noreply@example.com</email>
  </author>
  <description>{description}</description>
</model>
"""
        (model_dir / "model.config").write_text(config.strip() + "\n", encoding="utf-8")

    def _write_world_file(self) -> None:
        world_path = self.world_dir / "city.world"
        include_blocks = "\n".join(
            f"    <include>\n      <uri>file://{uri}</uri>\n    </include>" for uri in self.model_includes
        )
        world_contents = f"""
<?xml version='1.0'?>
<sdf version='1.9'>
  <world name='osm_city_world'>
    <gravity>0 0 -9.81</gravity>
    <magnetic_field>6e-06 2.3e-05 -4.2e-05</magnetic_field>
    <atmosphere type='constant'/>
    <scene>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.7 0.7 0.8 1</background>
      <shadows>true</shadows>
    </scene>
    <physics name='ode' type='ode'>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
      <max_step_size>0.001</max_step_size>
    </physics>
    <light name='sun' type='directional'>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>1 1 1 1</diffuse>
      <direction>-0.5 0.5 -1</direction>
    </light>
{include_blocks}
  </world>
</sdf>
"""
        world_path.write_text(world_contents.strip() + "\n", encoding="utf-8")

    def _write_spawn_points(self, segments: Sequence[Segment]) -> None:
        spawn_points = []
        for segment in segments:
            center_x = (segment.start[0] + segment.end[0]) / 2.0
            center_y = (segment.start[1] + segment.end[1]) / 2.0
            yaw = math.atan2(segment.end[1] - segment.start[1], segment.end[0] - segment.start[0])
            spawn_points.append(
                {
                    "x": center_x,
                    "y": center_y,
                    "z": 0.1,
                    "yaw": yaw,
                    "lane_id": segment.seg_id,
                }
            )
        self.spawn_file.write_text(json.dumps(spawn_points, indent=2), encoding="utf-8")

    def _write_camera_views(
        self,
        segments: Sequence[Segment],
        buildings: Sequence[Building],
        trees: Sequence[Tree],
    ) -> None:
        views = []
        if segments:
            # Long straight road
            longest = max(segments, key=lambda s: math.dist(s.start, s.end))
            center_x = (longest.start[0] + longest.end[0]) / 2.0
            center_y = (longest.start[1] + longest.end[1]) / 2.0
            yaw = math.atan2(longest.end[1] - longest.start[1], longest.end[0] - longest.start[0])
            views.append(
                self._camera_payload(
                    name="long_straight",
                    position=(center_x, center_y, 5.0),
                    yaw=yaw,
                    pitch=-0.25,
                    description="Long straight road"
                )
            )
            # Intersection overhead
            inter_node = self._find_intersection_node()
            if inter_node is not None:
                gx, gy = self.gazebo_nodes[inter_node]
            else:
                gx, gy = center_x, center_y
            views.append(
                self._camera_payload(
                    name="intersection_overhead",
                    position=(gx, gy, 60.0),
                    yaw=0.0,
                    pitch=-1.2,
                    description="Intersection overhead"
                )
            )
        if buildings:
            bld = buildings[0]
            views.append(
                self._camera_payload(
                    name="street_level_building",
                    position=(bld.centroid[0], bld.centroid[1] - 10.0, 3.0),
                    yaw=0.0,
                    pitch=-0.1,
                    description="Street-level building view"
                )
            )
        if trees:
            tree = trees[0]
            views.append(
                self._camera_payload(
                    name="tree_corridor",
                    position=(tree.position[0], tree.position[1] - 5.0, 4.0),
                    yaw=0.0,
                    pitch=-0.15,
                    description="Tree-lined road view"
                )
            )
        self.camera_file.write_text(json.dumps(views, indent=2), encoding="utf-8")

    def _camera_payload(self, name: str, position: Tuple[float, float, float], yaw: float, pitch: float, description: str) -> Dict[str, object]:
        return {
            "name": name,
            "description": description,
            "x": position[0],
            "y": position[1],
            "z": position[2],
            "yaw": yaw,
            "pitch": pitch,
            "roll": 0.0,
        }

    def _find_intersection_node(self) -> Optional[int]:
        candidates = [node_id for node_id, count in self.node_usage.items() if count >= 3]
        return candidates[0] if candidates else None


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a procedural Gazebo city from OSM data.")
    parser.add_argument("osm_file", type=Path, help="Path to the source OSM file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Target directory for generated assets (defaults to project root)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    osm_path = args.osm_file.resolve()
    if not osm_path.exists():
        raise FileNotFoundError(osm_path)
    output_dir = args.output_dir.resolve()
    builder = CityBuilder(osm_path=osm_path, output_root=output_dir)
    builder.run()


if __name__ == "__main__":
    main(sys.argv[1:])
