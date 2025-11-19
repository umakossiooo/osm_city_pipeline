#!/bin/bash
# Test suite to run INSIDE the container - tests Phase 1 & 2 functionality

set -e  # Exit on error

echo "============================================================"
echo "PHASE 1 & 2 FUNCTIONALITY TEST SUITE (Inside Container)"
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
    if eval "$command" > /tmp/test_output_$test_count.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Command: $command"
        echo "  Output:"
        cat /tmp/test_output_$test_count.log | sed 's/^/    /'
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Change to project directory
cd /workspace/osm_city_pipeline
export PYTHONPATH=/workspace/osm_city_pipeline/src

echo "=== PHASE 1 TESTS ==="
echo ""

# Test 1: Required folders exist
run_test "Required folder structure exists" \
    "test -d docker && test -d maps && test -d worlds && test -d src/osm_city_pipeline && test -d scripts && test -d config"

# Test 2: Required files exist
run_test "Required Phase 1 files exist" \
    "test -f docker/Dockerfile && test -f compose.yaml && test -f src/osm_city_pipeline/__init__.py && test -f src/osm_city_pipeline/cli.py && test -f scripts/generate_world.sh && test -f scripts/reset_world.sh && test -f config/pipeline_config.yaml && test -f README.md"

# Test 3: CLI can be imported
run_test "CLI module can be imported" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import cli'"

# Test 4: CLI shows help
run_test "CLI shows help message" \
    "python3 src/osm_city_pipeline/cli.py --help | grep -q 'OSM City Pipeline'"

echo ""
echo "=== PHASE 2 TESTS ==="
echo ""

# Test 5: pyproj is installed
run_test "pyproj is installed" \
    "python3 -c 'import pyproj; print(pyproj.__version__)' | grep -q '.'"

# Test 6: gis_projection module can be imported
run_test "gis_projection module can be imported" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import gis_projection'"

# Test 7: ENUProjection class exists
run_test "ENUProjection class is available" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import ENUProjection; assert ENUProjection is not None'"

# Test 8: project_to_enu function exists
run_test "project_to_enu function is available" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import project_to_enu; assert callable(project_to_enu)'"

# Test 9: OSM file exists
run_test "OSM test file (bari.osm) exists" \
    "test -f maps/bari.osm"

# Test 10: OSM bounds extraction works
run_test "OSM bounds extraction works" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import get_osm_bounds; bounds = get_osm_bounds(\"maps/bari.osm\"); assert bounds is not None and len(bounds) == 4'"

# Test 11: ENU projection creation from OSM
run_test "ENU projection creation from OSM file works" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); assert enu is not None'"

# Test 12: Center point projects to origin
run_test "Center point projects to (0,0,0)" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); e, n, u = enu.project_to_enu(enu.center_lat, enu.center_lon, 0); assert abs(e) < 0.001 and abs(n) < 0.001 and abs(u) < 0.001'"

# Test 13: CLI test-projection command works
run_test "CLI test-projection command executes" \
    "python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --height 0 | grep -q 'ENU Projection Results'"

# Test 14: CLI test-projection with OSM file
run_test "CLI test-projection with OSM file works" \
    "python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --osm-file maps/bari.osm | grep -q 'Projection center'"

# Test 15: Deterministic output
run_test "ENU projection produces deterministic output" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); r1 = enu.project_to_enu(41.122, 16.867, 0); r2 = enu.project_to_enu(41.122, 16.867, 0); assert abs(r1[0] - r2[0]) < 0.001 and abs(r1[1] - r2[1]) < 0.001'"

echo ""
echo "=== INTEGRATION TESTS ==="
echo ""

# Test 16: Full workflow: OSM -> ENU
run_test "Full workflow: Extract OSM bounds and project coordinates" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm, get_osm_bounds; bounds = get_osm_bounds(\"maps/bari.osm\"); enu = create_enu_from_osm(\"maps/bari.osm\"); minlat, minlon, maxlat, maxlon = bounds; center_lat = (minlat + maxlat) / 2; center_lon = (minlon + maxlon) / 2; e, n, u = enu.project_to_enu(center_lat, center_lon, 0); assert abs(e) < 0.001 and abs(n) < 0.001'"

# Test 17: Multiple coordinates project correctly
run_test "Multiple coordinates project to reasonable ENU values" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); e1, n1, u1 = enu.project_to_enu(41.124, 16.871, 0); e2, n2, u2 = enu.project_to_enu(41.119, 16.862, 0); assert e1 > 0 and n1 > 0 and e2 < 0 and n2 < 0'"

# Test 18: Height component works correctly
run_test "Height component correctly reflected in up coordinate" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); e1, n1, u1 = enu.project_to_enu(41.122, 16.867, 0); e2, n2, u2 = enu.project_to_enu(41.122, 16.867, 10); assert abs(e1 - e2) < 0.001 and abs(n1 - n2) < 0.001 and abs(u2 - u1 - 10) < 0.001'"

# Test 19: Convenience function works
run_test "Convenience function project_to_enu works with OSM file" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import project_to_enu; e, n, u = project_to_enu(41.122, 16.867, 0, osm_file_path=\"maps/bari.osm\"); assert isinstance(e, float) and isinstance(n, float) and isinstance(u, float)'"

# Test 20: All modules can be imported together
run_test "All Phase 1 and Phase 2 modules import together" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import cli, gis_projection, __init__; assert cli and gis_projection and __init__'"

# Test 21: Volume mounts work (files are accessible)
run_test "Volume mounts are working (files are accessible)" \
    "test -f /workspace/osm_city_pipeline/maps/bari.osm && test -f /workspace/osm_city_pipeline/src/osm_city_pipeline/cli.py"

# Test 22: CLI works with different coordinate combinations
run_test "CLI handles different coordinate combinations" \
    "python3 src/osm_city_pipeline/cli.py test-projection --lat 41.120 --lon 16.863 --center-lat 41.122 --center-lon 16.867 | grep -q 'ENU Projection Results'"

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
    echo -e "${GREEN}✓ ALL TESTS PASSED - PHASE 1 & 2 INTEGRATION VERIFIED${NC}"
    exit 0
fi

