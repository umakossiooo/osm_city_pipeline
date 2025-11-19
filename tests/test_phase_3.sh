#!/bin/bash
# Test suite for Phase 3 - OSM parsing and road extraction

set -e  # Exit on error

echo "============================================================"
echo "PHASE 3 TEST SUITE (OSM Parsing & Road Extraction)"
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
    if eval "$command" > /tmp/test_output_phase3_$test_count.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Command: $command"
        echo "  Output:"
        cat /tmp/test_output_phase3_$test_count.log | sed 's/^/    /'
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Change to project directory
cd /workspace/osm_city_pipeline
export PYTHONPATH=/workspace/osm_city_pipeline/src

echo "=== DEPENDENCY TESTS ==="
echo ""

# Test 1: osmium is installed
run_test "osmium is installed" \
    "python3 -c 'import osmium; print(\"osmium imported\")' | grep -q 'osmium imported'"

# Test 2: shapely is installed
run_test "shapely is installed" \
    "python3 -c 'import shapely; print(\"shapely imported\")' | grep -q 'shapely imported'"

echo ""
echo "=== MODULE IMPORT TESTS ==="
echo ""

# Test 3: osm_parser module can be imported
run_test "osm_parser module can be imported" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import osm_parser'"

# Test 4: road_extractor module can be imported
run_test "road_extractor module can be imported" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import road_extractor'"

echo ""
echo "=== OSM PARSING TESTS ==="
echo ""

# Test 5: OSM file can be parsed
run_test "OSM file can be parsed" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.osm_parser import parse_osm_file; nodes, ways, relations = parse_osm_file(\"maps/bari.osm\"); assert len(nodes) > 0 and len(ways) > 0'"

# Test 6: Parsed data structure is correct
run_test "Parsed data structure is correct" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.osm_parser import parse_osm_file; nodes, ways, relations = parse_osm_file(\"maps/bari.osm\"); assert isinstance(nodes, dict) and isinstance(ways, dict) and isinstance(relations, dict)'"

echo ""
echo "=== ROAD EXTRACTION TESTS ==="
echo ""

# Test 7: Highways can be extracted
run_test "Highways can be extracted" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.road_extractor import extract_highways; highways = extract_highways(\"maps/bari.osm\"); assert len(highways) > 0'"

# Test 8: Highway structure is correct
run_test "Highway structure is correct" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.road_extractor import extract_highways; highways = extract_highways(\"maps/bari.osm\"); hw = highways[0] if highways else None; assert hw and \"way_id\" in hw and \"name\" in hw and \"highway_type\" in hw and \"coordinates\" in hw'"

# Test 9: Intersections can be found
run_test "Intersections can be found" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.road_extractor import extract_road_metadata; metadata = extract_road_metadata(\"maps/bari.osm\"); assert len(metadata[\"intersections\"]) > 0'"

# Test 10: Lane centerlines can be extracted
run_test "Lane centerlines can be extracted" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.road_extractor import extract_road_metadata; metadata = extract_road_metadata(\"maps/bari.osm\"); assert len(metadata[\"lane_centerlines\"]) > 0'"

echo ""
echo "=== JSON OUTPUT TESTS ==="
echo ""

# Test 11: Metadata can be saved to JSON
run_test "Metadata can be saved to JSON" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.road_extractor import extract_and_save_road_metadata; import os; metadata = extract_and_save_road_metadata(\"maps/bari.osm\", \"/tmp/test_metadata.json\"); assert os.path.exists(\"/tmp/test_metadata.json\")'"

# Test 12: JSON file is valid
run_test "JSON file is valid" \
    "python3 -c 'import json; data = json.load(open(\"/tmp/test_metadata.json\")); assert \"highways\" in data and \"intersections\" in data and \"lane_centerlines\" in data and \"summary\" in data'"

# Test 13: JSON contains required fields
run_test "JSON contains required fields" \
    "python3 -c 'import json; data = json.load(open(\"/tmp/test_metadata.json\")); hw = data[\"highways\"][0] if data[\"highways\"] else None; assert hw and \"way_id\" in hw and \"name\" in hw and \"highway_type\" in hw and \"coordinates\" in hw'"

echo ""
echo "=== CLI TESTS ==="
echo ""

# Test 14: extract-roads command exists
run_test "extract-roads command exists" \
    "python3 src/osm_city_pipeline/cli.py --help | grep -q 'extract-roads'"

# Test 15: extract-roads command executes
run_test "extract-roads command executes" \
    "python3 src/osm_city_pipeline/cli.py extract-roads --osm-file maps/bari.osm --output /tmp/test_cli_output.json | grep -q 'Road Extraction Summary'"

# Test 16: CLI output JSON is valid
run_test "CLI output JSON is valid" \
    "python3 -c 'import json; data = json.load(open(\"/tmp/test_cli_output.json\")); assert \"highways\" in data'"

echo ""
echo "=== INTEGRATION WITH PHASE 1 & 2 ==="
echo ""

# Test 17: All phases import together
run_test "All phases import together" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import cli, gis_projection, osm_parser, road_extractor; assert cli and gis_projection and osm_parser and road_extractor'"

# Test 18: Phase 2 + Phase 3 integration
run_test "Phase 2 + Phase 3 integration (ENU + roads)" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; from osm_city_pipeline.road_extractor import extract_road_metadata; enu = create_enu_from_osm(\"maps/bari.osm\"); metadata = extract_road_metadata(\"maps/bari.osm\"); hw = metadata[\"highways\"][0] if metadata[\"highways\"] else None; assert hw; lat, lon = hw[\"coordinates\"][0]; e, n, u = enu.project_to_enu(lat, lon, 0); assert isinstance(e, float)'"

# Test 19: Named roads are extracted
run_test "Named roads are extracted" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.road_extractor import extract_road_metadata; metadata = extract_road_metadata(\"maps/bari.osm\"); named = [hw for hw in metadata[\"highways\"] if hw[\"name\"]]; assert len(named) > 0'"

# Test 20: Way IDs are preserved
run_test "Way IDs are preserved" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.road_extractor import extract_road_metadata; metadata = extract_road_metadata(\"maps/bari.osm\"); hw = metadata[\"highways\"][0] if metadata[\"highways\"] else None; assert hw and isinstance(hw[\"way_id\"], (int, str))'"

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
    echo -e "${GREEN}✓ ALL PHASE 3 TESTS PASSED${NC}"
    exit 0
fi

