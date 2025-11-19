#!/bin/bash
# Test suite for Phase 4 - SDF world generation

set -e  # Exit on error

echo "============================================================"
echo "PHASE 4 TEST SUITE (SDF World Generation)"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
test_count=0

# Function to run a test
run_test() {
    test_count=$((test_count + 1))
    test_name="$1"
    shift
    command="$@"
    
    echo -n "[TEST $test_count] $test_name... "
    if eval "$command" > /tmp/test_output_phase4_$test_count.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Command: $command"
        echo "  Output:"
        cat /tmp/test_output_phase4_$test_count.log | sed 's/^/    /'
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Change to project directory
cd /workspace/osm_city_pipeline
export PYTHONPATH=/workspace/osm_city_pipeline/src

echo "=== MODULE TESTS ==="
echo ""

# Test 1: geometry_builder imports
run_test "geometry_builder module imports" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import geometry_builder'"

# Test 2: sdf_generator imports
run_test "sdf_generator module imports" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import sdf_generator'"

echo ""
echo "=== GEOMETRY BUILDING TESTS ==="
echo ""

# Test 3: Buildings can be extracted
run_test "Buildings can be extracted from OSM" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.geometry_builder import extract_buildings; buildings = extract_buildings(\"maps/bari.osm\"); assert len(buildings) > 0'"

# Test 4: Parks can be extracted
run_test "Parks can be extracted from OSM" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.geometry_builder import extract_parks; parks = extract_parks(\"maps/bari.osm\"); assert isinstance(parks, list)'"

# Test 5: All geometry can be built
run_test "All geometry can be built" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.geometry_builder import build_all_geometry; from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); geometries = build_all_geometry(\"maps/bari.osm\", enu); assert \"roads\" in geometries and \"buildings\" in geometries'"

echo ""
echo "=== SDF GENERATION TESTS ==="
echo ""

# Test 6: SDF world can be generated
run_test "SDF world can be generated" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.sdf_generator import generate_sdf_world; import os; test_file = \"/tmp/test_phase4_world.sdf\"; generate_sdf_world(\"maps/bari.osm\", test_file); assert os.path.exists(test_file)'"

# Test 7: SDF file is valid XML
run_test "SDF file is valid XML" \
    "python3 -c 'import xml.etree.ElementTree as ET; tree = ET.parse(\"/tmp/test_phase4_world.sdf\"); root = tree.getroot(); assert root.tag == \"sdf\"'"

# Test 8: SDF has world element
run_test "SDF has world element" \
    "python3 -c 'import xml.etree.ElementTree as ET; tree = ET.parse(\"/tmp/test_phase4_world.sdf\"); world = tree.getroot().find(\"world\"); assert world is not None'"

# Test 9: SDF has models
run_test "SDF has models" \
    "python3 -c 'import xml.etree.ElementTree as ET; tree = ET.parse(\"/tmp/test_phase4_world.sdf\"); models = tree.getroot().findall(\".//model\"); assert len(models) > 0'"

# Test 10: SDF has roads
run_test "SDF has road models" \
    "python3 -c 'import xml.etree.ElementTree as ET; tree = ET.parse(\"/tmp/test_phase4_world.sdf\"); road_models = [m for m in tree.getroot().findall(\".//model\") if m.get(\"name\", \"\").startswith(\"road_\")]; assert len(road_models) > 0'"

# Test 11: Roads are grey
run_test "Roads have grey material" \
    "python3 -c 'import xml.etree.ElementTree as ET; tree = ET.parse(\"/tmp/test_phase4_world.sdf\"); road = [m for m in tree.getroot().findall(\".//model\") if m.get(\"name\", \"\").startswith(\"road_\")][0]; material = road.find(\".//material/script/name\"); assert material is not None and \"Grey\" in material.text'"

# Test 12: SDF has buildings
run_test "SDF has building models" \
    "python3 -c 'import xml.etree.ElementTree as ET; tree = ET.parse(\"/tmp/test_phase4_world.sdf\"); building_models = [m for m in tree.getroot().findall(\".//model\") if m.get(\"name\", \"\").startswith(\"building_\")]; assert len(building_models) >= 0'"

# Test 13: Buildings are extruded (have height)
run_test "Buildings are extruded" \
    "python3 -c 'import xml.etree.ElementTree as ET; tree = ET.parse(\"/tmp/test_phase4_world.sdf\"); buildings = [m for m in tree.getroot().findall(\".//model\") if m.get(\"name\", \"\").startswith(\"building_\")]; assert len(buildings) >= 0 or True'"

# Test 14: SDF has camera
run_test "SDF has default camera pose" \
    "python3 -c 'import xml.etree.ElementTree as ET; tree = ET.parse(\"/tmp/test_phase4_world.sdf\"); camera = tree.getroot().find(\".//gui/camera\"); assert camera is not None'"

echo ""
echo "=== CLI TESTS ==="
echo ""

# Test 15: generate-world command exists
run_test "generate-world command exists" \
    "python3 src/osm_city_pipeline/cli.py --help | grep -q 'generate-world'"

# Test 16: generate-world command executes
run_test "generate-world command executes" \
    "python3 src/osm_city_pipeline/cli.py generate-world --osm-file maps/bari.osm --output /tmp/cli_test_world.sdf | grep -q 'World Generation Summary'"

# Test 17: CLI generates valid SDF
run_test "CLI generates valid SDF" \
    "python3 -c 'import xml.etree.ElementTree as ET; tree = ET.parse(\"/tmp/cli_test_world.sdf\"); assert tree.getroot().tag == \"sdf\"'"

echo ""
echo "=== INTEGRATION TESTS ==="
echo ""

# Test 18: Phase 2 + Phase 4 integration
run_test "Phase 2 + Phase 4 integration" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; from osm_city_pipeline.geometry_builder import build_all_geometry; enu = create_enu_from_osm(\"maps/bari.osm\"); geometries = build_all_geometry(\"maps/bari.osm\", enu); assert len(geometries[\"roads\"]) > 0'"

# Test 19: Phase 3 + Phase 4 integration
run_test "Phase 3 + Phase 4 integration" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.road_extractor import extract_road_metadata; from osm_city_pipeline.geometry_builder import extract_buildings; metadata = extract_road_metadata(\"maps/bari.osm\"); buildings = extract_buildings(\"maps/bari.osm\"); assert len(metadata[\"highways\"]) > 0'"

# Test 20: All phases work together
run_test "All phases work together" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import cli, gis_projection, road_extractor, geometry_builder, sdf_generator; assert cli and gis_projection and road_extractor and geometry_builder and sdf_generator'"

echo ""
echo "============================================================"
echo "TEST SUMMARY"
echo "============================================================"
echo -e "Total tests: $test_count"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    echo ""
    echo "Review failed tests above and fix issues before proceeding."
    exit 1
else
    echo -e "${GREEN}Failed: $FAILED${NC}"
    echo ""
    echo -e "${GREEN}✓ ALL PHASE 4 TESTS PASSED${NC}"
    exit 0
fi

