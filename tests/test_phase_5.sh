#!/bin/bash
# Test suite for Phase 5 - Metadata export

set -e  # Exit on error

echo "============================================================"
echo "PHASE 5 TEST SUITE (Metadata Export)"
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
    if eval "$command" > /tmp/test_output_phase5_$test_count.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Command: $command"
        echo "  Output:"
        cat /tmp/test_output_phase5_$test_count.log | sed 's/^/    /'
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Change to project directory
cd /workspace/osm_city_pipeline
export PYTHONPATH=/workspace/osm_city_pipeline/src

echo "=== MODULE TESTS ==="
echo ""

# Test 1: metadata_exporter imports
run_test "metadata_exporter module imports" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import metadata_exporter'"

# Test 2: yaml installed
run_test "yaml module available" \
    "python3 -c 'import yaml'"

echo ""
echo "=== METADATA EXPORT TESTS ==="
echo ""

# Test 3: Export roads.json
run_test "roads.json can be exported" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.metadata_exporter import export_roads_json; import os; test_file = \"/tmp/test_roads.json\"; export_roads_json(\"maps/bari.osm\", test_file); assert os.path.exists(test_file)'"

# Test 4: roads.json is valid JSON
run_test "roads.json is valid JSON" \
    "python3 -c 'import json; data = json.load(open(\"/tmp/test_roads.json\")); assert \"roads\" in data and \"projection_center\" in data'"

# Test 5: roads.json has roads
run_test "roads.json contains roads" \
    "python3 -c 'import json; data = json.load(open(\"/tmp/test_roads.json\")); assert len(data[\"roads\"]) > 0'"

# Test 6: roads.json has ENU coordinates
run_test "roads.json has ENU coordinates" \
    "python3 -c 'import json; data = json.load(open(\"/tmp/test_roads.json\")); road = data[\"roads\"][0]; assert \"centerline_enu\" in road and len(road[\"centerline_enu\"]) > 0'"

# Test 7: Export spawn_points.yaml
run_test "spawn_points.yaml can be exported" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.metadata_exporter import export_spawn_points_yaml; import os; test_file = \"/tmp/test_spawn.yaml\"; export_spawn_points_yaml(\"maps/bari.osm\", test_file); assert os.path.exists(test_file)'"

# Test 8: spawn_points.yaml is valid YAML
run_test "spawn_points.yaml is valid YAML" \
    "python3 -c 'import yaml; data = yaml.safe_load(open(\"/tmp/test_spawn.yaml\")); assert \"spawn_points\" in data'"

# Test 9: spawn_points.yaml has spawn points
run_test "spawn_points.yaml contains spawn points" \
    "python3 -c 'import yaml; data = yaml.safe_load(open(\"/tmp/test_spawn.yaml\")); assert len(data[\"spawn_points\"]) > 0'"

# Test 10: Spawn points have ENU coordinates
run_test "Spawn points have ENU coordinates" \
    "python3 -c 'import yaml; data = yaml.safe_load(open(\"/tmp/test_spawn.yaml\")); sp = data[\"spawn_points\"][0]; assert \"position\" in sp and \"east\" in sp[\"position\"] and \"north\" in sp[\"position\"]'"

echo ""
echo "=== COORDINATE ALIGNMENT TESTS ==="
echo ""

# Test 11: Roads.json ENU matches projection
run_test "roads.json ENU coordinates match projection" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); import json; from osm_city_pipeline.gis_projection import create_enu_from_osm; from osm_city_pipeline.road_extractor import extract_road_metadata; enu = create_enu_from_osm(\"maps/bari.osm\"); metadata = extract_road_metadata(\"maps/bari.osm\"); hw = metadata[\"highways\"][0]; lat, lon = hw[\"coordinates\"][0]; e1, n1, u1 = enu.project_to_enu(lat, lon, 0.0); data = json.load(open(\"/tmp/test_roads.json\")); road = data[\"roads\"][0]; e2, n2, u2 = road[\"centerline_enu\"][0][\"east\"], road[\"centerline_enu\"][0][\"north\"], road[\"centerline_enu\"][0][\"up\"]; assert abs(e1 - e2) < 0.001 and abs(n1 - n2) < 0.001'"

# Test 12: Spawn points are on roads
run_test "Spawn points are on road segments" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); import json; import yaml; import math; roads_data = json.load(open(\"/tmp/test_roads.json\")); spawn_data = yaml.safe_load(open(\"/tmp/test_spawn.yaml\")); sp = spawn_data[\"spawn_points\"][0]; road = next((r for r in roads_data[\"roads\"] if r[\"way_id\"] == sp[\"way_id\"]), None); assert road is not None; min_dist = float(\"inf\"); [min_dist := min(min_dist, math.sqrt((p[\"east\"] - sp[\"position\"][\"east\"])**2 + (p[\"north\"] - sp[\"position\"][\"north\"])**2)) for p in road[\"centerline_enu\"]]; assert min_dist < 5.0'"

echo ""
echo "=== CLI TESTS ==="
echo ""

# Test 13: export-metadata command exists
run_test "export-metadata command exists" \
    "python3 src/osm_city_pipeline/cli.py --help | grep -q 'export-metadata'"

# Test 14: export-metadata command executes
run_test "export-metadata command executes" \
    "python3 src/osm_city_pipeline/cli.py export-metadata --osm-file maps/bari.osm --roads-output /tmp/cli_roads.json --spawn-output /tmp/cli_spawn.yaml | grep -q 'Metadata Export Summary'"

# Test 15: CLI generates valid files
run_test "CLI generates valid metadata files" \
    "python3 -c 'import json; import yaml; json.load(open(\"/tmp/cli_roads.json\")); yaml.safe_load(open(\"/tmp/cli_spawn.yaml\"))'"

echo ""
echo "=== DETERMINISTIC BEHAVIOR TESTS (RULE 5) ==="
echo ""

# Test 16: Multiple exports produce same results
run_test "Multiple exports produce identical results" \
    "python3 << 'PYEOF'
import sys
sys.path.insert(0, 'src')
import json
import yaml
import subprocess
import os

# Export twice
for i in range(2):
    test_roads = f'/tmp/det_test_{i}_roads.json'
    test_spawn = f'/tmp/det_test_{i}_spawn.yaml'
    if os.path.exists(test_roads):
        os.remove(test_roads)
    if os.path.exists(test_spawn):
        os.remove(test_spawn)
    
    subprocess.run(['python3', 'src/osm_city_pipeline/cli.py', 'export-metadata',
                    '--osm-file', 'maps/bari.osm',
                    '--roads-output', test_roads,
                    '--spawn-output', test_spawn],
                   check=True, cwd='/workspace/osm_city_pipeline',
                   env={'PYTHONPATH': '/workspace/osm_city_pipeline/src'})

# Compare
data1 = json.load(open('/tmp/det_test_0_roads.json'))
data2 = json.load(open('/tmp/det_test_1_roads.json'))
assert len(data1['roads']) == len(data2['roads'])
p1 = data1['roads'][0]['centerline_enu'][0]
p2 = data2['roads'][0]['centerline_enu'][0]
assert abs(p1['east'] - p2['east']) < 0.001
PYEOF
"

echo ""
echo "=== INTEGRATION TESTS ==="
echo ""

# Test 17: Phase 2 + Phase 5 integration
run_test "Phase 2 + Phase 5 integration" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; from osm_city_pipeline.metadata_exporter import export_roads_json; enu = create_enu_from_osm(\"maps/bari.osm\"); export_roads_json(\"maps/bari.osm\", \"/tmp/int_test_roads.json\"); import json; data = json.load(open(\"/tmp/int_test_roads.json\")); assert data[\"projection_center\"][\"latitude\"] == enu.center_lat'"

# Test 18: Phase 3 + Phase 5 integration
run_test "Phase 3 + Phase 5 integration" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.road_extractor import extract_road_metadata; from osm_city_pipeline.metadata_exporter import export_roads_json; metadata = extract_road_metadata(\"maps/bari.osm\"); export_roads_json(\"maps/bari.osm\", \"/tmp/int_test_roads2.json\"); import json; data = json.load(open(\"/tmp/int_test_roads2.json\")); assert len(data[\"roads\"]) == len(metadata[\"lane_centerlines\"])'"

# Test 19: Phase 4 + Phase 5 integration
run_test "Phase 4 + Phase 5 integration" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.sdf_generator import generate_sdf_world; from osm_city_pipeline.metadata_exporter import export_all_metadata; import os; generate_sdf_world(\"maps/bari.osm\", \"/tmp/int_test_world.sdf\"); export_all_metadata(\"maps/bari.osm\", \"/tmp/int_test_roads3.json\", \"/tmp/int_test_spawn3.yaml\"); assert os.path.exists(\"/tmp/int_test_world.sdf\") and os.path.exists(\"/tmp/int_test_roads3.json\")'"

# Test 20: All phases work together
run_test "All phases work together" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import gis_projection, road_extractor, sdf_generator, metadata_exporter; assert all([gis_projection, road_extractor, sdf_generator, metadata_exporter])'"

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
    echo -e "${GREEN}✓ ALL PHASE 5 TESTS PASSED${NC}"
    exit 0
fi

