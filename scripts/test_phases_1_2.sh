#!/bin/bash
# Comprehensive test suite for Phase 1 and Phase 2 integration

set -e  # Exit on error

echo "============================================================"
echo "PHASE 1 & 2 INTEGRATION TEST SUITE"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test counter
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

# Test 1: Docker image exists (build verification done separately)
run_test "Docker image exists" \
    "docker images | grep -q 'osm_city_pipeline' || docker compose build > /dev/null 2>&1"

# Test 2: Docker compose container is running
run_test "Docker compose container is running" \
    "docker compose ps 2>/dev/null | grep -q 'Up' || (docker compose up -d > /dev/null 2>&1 && sleep 3 && docker compose ps | grep -q 'Up')"

# Test 3: Required folders exist
run_test "Required folder structure exists" \
    "test -d docker && test -d maps && test -d worlds && test -d src/osm_city_pipeline && test -d scripts && test -d config"

# Test 4: Required files exist
run_test "Required Phase 1 files exist" \
    "test -f docker/Dockerfile && test -f compose.yaml && test -f src/osm_city_pipeline/__init__.py && test -f src/osm_city_pipeline/cli.py && test -f scripts/generate_world.sh && test -f scripts/reset_world.sh && test -f config/pipeline_config.yaml && test -f README.md"

# Test 5: CLI can be imported
run_test "CLI module can be imported" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import cli'"

# Test 6: CLI shows help
run_test "CLI shows help message" \
    "python3 src/osm_city_pipeline/cli.py --help | grep -q 'OSM City Pipeline'"

echo ""
echo "=== PHASE 2 TESTS ==="
echo ""

# Test 7: pyproj is installed
run_test "pyproj is installed in container" \
    "python3 -c 'import pyproj; print(pyproj.__version__)' | grep -q '.'"

# Test 8: gis_projection module can be imported
run_test "gis_projection module can be imported" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import gis_projection'"

# Test 9: ENUProjection class exists
run_test "ENUProjection class is available" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import ENUProjection; assert ENUProjection is not None'"

# Test 10: project_to_enu function exists
run_test "project_to_enu function is available" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import project_to_enu; assert callable(project_to_enu)'"

# Test 11: OSM file exists
run_test "OSM test file (bari.osm) exists" \
    "test -f maps/bari.osm"

# Test 12: OSM bounds extraction works
run_test "OSM bounds extraction works" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import get_osm_bounds; bounds = get_osm_bounds(\"maps/bari.osm\"); assert bounds is not None and len(bounds) == 4'"

# Test 13: ENU projection creation from OSM
run_test "ENU projection creation from OSM file works" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); assert enu is not None'"

# Test 14: Center point projects to origin
run_test "Center point projects to (0,0,0)" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); e, n, u = enu.project_to_enu(enu.center_lat, enu.center_lon, 0); assert abs(e) < 0.001 and abs(n) < 0.001 and abs(u) < 0.001'"

# Test 15: CLI test-projection command works
run_test "CLI test-projection command executes" \
    "python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --height 0 | grep -q 'ENU Projection Results'"

# Test 16: CLI test-projection with OSM file
run_test "CLI test-projection with OSM file works" \
    "python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --osm-file maps/bari.osm | grep -q 'Projection center'"

# Test 17: Deterministic output
run_test "ENU projection produces deterministic output" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); r1 = enu.project_to_enu(41.122, 16.867, 0); r2 = enu.project_to_enu(41.122, 16.867, 0); assert abs(r1[0] - r2[0]) < 0.001 and abs(r1[1] - r2[1]) < 0.001'"

echo ""
echo "=== INTEGRATION TESTS ==="
echo ""

# Test 18: CLI works from container entry point
run_test "CLI works when called from container" \
    "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --height 0' | grep -q 'ENU Projection Results'"

# Test 19: Full workflow: OSM -> ENU
run_test "Full workflow: Extract OSM bounds and project coordinates" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm, get_osm_bounds; bounds = get_osm_bounds(\"maps/bari.osm\"); enu = create_enu_from_osm(\"maps/bari.osm\"); minlat, minlon, maxlat, maxlon = bounds; center_lat = (minlat + maxlat) / 2; center_lon = (minlon + maxlon) / 2; e, n, u = enu.project_to_enu(center_lat, center_lon, 0); assert abs(e) < 0.001 and abs(n) < 0.001'"

# Test 20: Multiple coordinates project correctly
run_test "Multiple coordinates project to reasonable ENU values" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); e1, n1, u1 = enu.project_to_enu(41.124, 16.871, 0); e2, n2, u2 = enu.project_to_enu(41.119, 16.862, 0); assert e1 > 0 and n1 > 0 and e2 < 0 and n2 < 0'"

# Test 21: Height component works correctly
run_test "Height component correctly reflected in up coordinate" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); e1, n1, u1 = enu.project_to_enu(41.122, 16.867, 0); e2, n2, u2 = enu.project_to_enu(41.122, 16.867, 10); assert abs(e1 - e2) < 0.001 and abs(n1 - n2) < 0.001 and abs(u2 - u1 - 10) < 0.001'"

# Test 22: Convenience function works
run_test "Convenience function project_to_enu works with OSM file" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import project_to_enu; e, n, u = project_to_enu(41.122, 16.867, 0, osm_file_path=\"maps/bari.osm\"); assert isinstance(e, float) and isinstance(n, float) and isinstance(u, float)'"

# Test 23: All modules can be imported together
run_test "All Phase 1 and Phase 2 modules import together" \
    "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import cli, gis_projection, __init__; assert cli and gis_projection and __init__'"

# Test 24: Container persists and is accessible
run_test "Container is running and accessible" \
    "docker compose ps | grep -q 'Up' && docker compose exec -T osm_city_pipeline echo 'test' | grep -q 'test'"

# Test 25: Volume mounts work
run_test "Volume mounts are working (files are accessible)" \
    "docker compose exec -T osm_city_pipeline test -f /workspace/osm_city_pipeline/maps/bari.osm && docker compose exec -T osm_city_pipeline test -f /workspace/osm_city_pipeline/src/osm_city_pipeline/cli.py"

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

