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

# Determine if running on host or in container
if [ -d "/workspace/osm_city_pipeline" ]; then
    # Running inside container
    cd /workspace/osm_city_pipeline
    export PYTHONPATH=/workspace/osm_city_pipeline/src
    CONTAINER_MODE=true
else
    # Running on host - need to use docker compose
    cd "$(dirname "$0")/.."
    CONTAINER_MODE=false
fi

echo "=== PHASE 1 TESTS ==="
echo ""

# Test 1: Docker image exists (build verification done separately)
if [ "$CONTAINER_MODE" = "false" ]; then
    run_test "Docker image exists" \
        "docker images | grep -q 'osm_city_pipeline' || docker compose build > /dev/null 2>&1"
    
    # Test 2: Docker compose container is running
    run_test "Docker compose container is running" \
        "docker compose ps 2>/dev/null | grep -q 'Up' || (docker compose up -d > /dev/null 2>&1 && sleep 3 && docker compose ps | grep -q 'Up')"
    
    # Run remaining tests inside container
    run_test "Required folder structure exists" \
        "docker compose exec -T osm_city_pipeline test -d docker && docker compose exec -T osm_city_pipeline test -d maps && docker compose exec -T osm_city_pipeline test -d worlds && docker compose exec -T osm_city_pipeline test -d src/osm_city_pipeline && docker compose exec -T osm_city_pipeline test -d scripts && docker compose exec -T osm_city_pipeline test -d config"
    
    run_test "Required Phase 1 files exist" \
        "docker compose exec -T osm_city_pipeline test -f docker/Dockerfile && docker compose exec -T osm_city_pipeline test -f compose.yaml && docker compose exec -T osm_city_pipeline test -f src/osm_city_pipeline/__init__.py && docker compose exec -T osm_city_pipeline test -f src/osm_city_pipeline/cli.py && docker compose exec -T osm_city_pipeline test -f scripts/generate_world.sh && docker compose exec -T osm_city_pipeline test -f scripts/reset_world.sh && docker compose exec -T osm_city_pipeline test -f config/pipeline_config.yaml && docker compose exec -T osm_city_pipeline test -f README.md"
    
    run_test "CLI module can be imported" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline import cli\"'"
    
    run_test "CLI shows help message" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 src/osm_city_pipeline/cli.py --help' | grep -q 'OSM City Pipeline'"
else
    # Running inside container
    run_test "Required folder structure exists" \
        "test -d docker && test -d maps && test -d worlds && test -d src/osm_city_pipeline && test -d scripts && test -d config"
    
    run_test "Required Phase 1 files exist" \
        "test -f docker/Dockerfile && test -f compose.yaml && test -f src/osm_city_pipeline/__init__.py && test -f src/osm_city_pipeline/cli.py && test -f scripts/generate_world.sh && test -f scripts/reset_world.sh && test -f config/pipeline_config.yaml && test -f README.md"
    
    run_test "CLI module can be imported" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import cli'"
    
    run_test "CLI shows help message" \
        "python3 src/osm_city_pipeline/cli.py --help | grep -q 'OSM City Pipeline'"
fi

echo ""
echo "=== PHASE 2 TESTS ==="
echo ""

# Test 7: pyproj is installed
if [ "$CONTAINER_MODE" = "false" ]; then
    run_test "pyproj is installed in container" \
        "docker compose exec -T osm_city_pipeline python3 -c 'import pyproj; print(pyproj.__version__)' | grep -q '.'"
    
    run_test "gis_projection module can be imported" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline import gis_projection\"'"
    
    run_test "ENUProjection class is available" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import ENUProjection; assert ENUProjection is not None\"'"
    
    run_test "project_to_enu function is available" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import project_to_enu; assert callable(project_to_enu)\"'"
    
    run_test "OSM test file (bari.osm) exists" \
        "docker compose exec -T osm_city_pipeline test -f maps/bari.osm"
    
    run_test "OSM bounds extraction works" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import get_osm_bounds; bounds = get_osm_bounds(\\\"maps/bari.osm\\\"); assert bounds is not None and len(bounds) == 4\"'"
    
    run_test "ENU projection creation from OSM file works" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\\\"maps/bari.osm\\\"); assert enu is not None\"'"
    
    run_test "Center point projects to (0,0,0)" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\\\"maps/bari.osm\\\"); e, n, u = enu.project_to_enu(enu.center_lat, enu.center_lon, 0); assert abs(e) < 0.001 and abs(n) < 0.001 and abs(u) < 0.001\"'"
    
    run_test "CLI test-projection command executes" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --height 0' | grep -q 'ENU Projection Results'"
    
    run_test "CLI test-projection with OSM file works" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --osm-file maps/bari.osm' | grep -q 'Projection center'"
    
    run_test "ENU projection produces deterministic output" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\\\"maps/bari.osm\\\"); r1 = enu.project_to_enu(41.122, 16.867, 0); r2 = enu.project_to_enu(41.122, 16.867, 0); assert abs(r1[0] - r2[0]) < 0.001 and abs(r1[1] - r2[1]) < 0.001\"'"
else
    run_test "pyproj is installed in container" \
        "python3 -c 'import pyproj; print(pyproj.__version__)' | grep -q '.'"
    
    run_test "gis_projection module can be imported" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import gis_projection'"
    
    run_test "ENUProjection class is available" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import ENUProjection; assert ENUProjection is not None'"
    
    run_test "project_to_enu function is available" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import project_to_enu; assert callable(project_to_enu)'"
    
    run_test "OSM test file (bari.osm) exists" \
        "test -f maps/bari.osm"
    
    run_test "OSM bounds extraction works" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import get_osm_bounds; bounds = get_osm_bounds(\"maps/bari.osm\"); assert bounds is not None and len(bounds) == 4'"
    
    run_test "ENU projection creation from OSM file works" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); assert enu is not None'"
    
    run_test "Center point projects to (0,0,0)" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); e, n, u = enu.project_to_enu(enu.center_lat, enu.center_lon, 0); assert abs(e) < 0.001 and abs(n) < 0.001 and abs(u) < 0.001'"
    
    run_test "CLI test-projection command executes" \
        "python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --height 0 | grep -q 'ENU Projection Results'"
    
    run_test "CLI test-projection with OSM file works" \
        "python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --osm-file maps/bari.osm | grep -q 'Projection center'"
    
    run_test "ENU projection produces deterministic output" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); r1 = enu.project_to_enu(41.122, 16.867, 0); r2 = enu.project_to_enu(41.122, 16.867, 0); assert abs(r1[0] - r2[0]) < 0.001 and abs(r1[1] - r2[1]) < 0.001'"
fi

echo ""
echo "=== INTEGRATION TESTS ==="
echo ""

# Test 18: CLI works from container entry point
if [ "$CONTAINER_MODE" = "false" ]; then
    run_test "CLI works when called from container" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 src/osm_city_pipeline/cli.py test-projection --lat 41.122 --lon 16.867 --height 0' | grep -q 'ENU Projection Results'"
    
    run_test "Full workflow: Extract OSM bounds and project coordinates" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import create_enu_from_osm, get_osm_bounds; bounds = get_osm_bounds(\\\"maps/bari.osm\\\"); enu = create_enu_from_osm(\\\"maps/bari.osm\\\"); minlat, minlon, maxlat, maxlon = bounds; center_lat = (minlat + maxlat) / 2; center_lon = (minlon + maxlon) / 2; e, n, u = enu.project_to_enu(center_lat, center_lon, 0); assert abs(e) < 0.001 and abs(n) < 0.001\"'"
    
    run_test "Multiple coordinates project to reasonable ENU values" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\\\"maps/bari.osm\\\"); e1, n1, u1 = enu.project_to_enu(41.124, 16.871, 0); e2, n2, u2 = enu.project_to_enu(41.119, 16.862, 0); assert e1 > 0 and n1 > 0 and e2 < 0 and n2 < 0\"'"
    
    run_test "Height component correctly reflected in up coordinate" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\\\"maps/bari.osm\\\"); e1, n1, u1 = enu.project_to_enu(41.122, 16.867, 0); e2, n2, u2 = enu.project_to_enu(41.122, 16.867, 10); assert abs(e1 - e2) < 0.001 and abs(n1 - n2) < 0.001 and abs(u2 - u1 - 10) < 0.001\"'"
    
    run_test "Convenience function project_to_enu works with OSM file" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline.gis_projection import project_to_enu; e, n, u = project_to_enu(41.122, 16.867, 0, osm_file_path=\\\"maps/bari.osm\\\"); assert isinstance(e, float) and isinstance(n, float) and isinstance(u, float)\"'"
    
    run_test "All Phase 1 and Phase 2 modules import together" \
        "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 -c \"import sys; sys.path.insert(0, \\\"src\\\"); from osm_city_pipeline import cli, gis_projection, __init__; assert cli and gis_projection and __init__\"'"
    
    run_test "Container is running and accessible" \
        "docker compose ps | grep -q 'Up' && docker compose exec -T osm_city_pipeline echo 'test' | grep -q 'test'"
    
    run_test "Volume mounts are working (files are accessible)" \
        "docker compose exec -T osm_city_pipeline test -f /workspace/osm_city_pipeline/maps/bari.osm && docker compose exec -T osm_city_pipeline test -f /workspace/osm_city_pipeline/src/osm_city_pipeline/cli.py"
else
    run_test "Full workflow: Extract OSM bounds and project coordinates" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm, get_osm_bounds; bounds = get_osm_bounds(\"maps/bari.osm\"); enu = create_enu_from_osm(\"maps/bari.osm\"); minlat, minlon, maxlat, maxlon = bounds; center_lat = (minlat + maxlat) / 2; center_lon = (minlon + maxlon) / 2; e, n, u = enu.project_to_enu(center_lat, center_lon, 0); assert abs(e) < 0.001 and abs(n) < 0.001'"
    
    run_test "Multiple coordinates project to reasonable ENU values" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); e1, n1, u1 = enu.project_to_enu(41.124, 16.871, 0); e2, n2, u2 = enu.project_to_enu(41.119, 16.862, 0); assert e1 > 0 and n1 > 0 and e2 < 0 and n2 < 0'"
    
    run_test "Height component correctly reflected in up coordinate" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import create_enu_from_osm; enu = create_enu_from_osm(\"maps/bari.osm\"); e1, n1, u1 = enu.project_to_enu(41.122, 16.867, 0); e2, n2, u2 = enu.project_to_enu(41.122, 16.867, 10); assert abs(e1 - e2) < 0.001 and abs(n1 - n2) < 0.001 and abs(u2 - u1 - 10) < 0.001'"
    
    run_test "Convenience function project_to_enu works with OSM file" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline.gis_projection import project_to_enu; e, n, u = project_to_enu(41.122, 16.867, 0, osm_file_path=\"maps/bari.osm\"); assert isinstance(e, float) and isinstance(n, float) and isinstance(u, float)'"
    
    run_test "All Phase 1 and Phase 2 modules import together" \
        "python3 -c 'import sys; sys.path.insert(0, \"src\"); from osm_city_pipeline import cli, gis_projection, __init__; assert cli and gis_projection and __init__'"
fi

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

