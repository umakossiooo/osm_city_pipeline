#!/bin/bash
# Test suite to run on HOST - tests Docker setup

set -e  # Exit on error

echo "============================================================"
echo "PHASE 1 DOCKER SETUP TEST SUITE (On Host)"
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
    if eval "$command" > /tmp/test_output_host_$test_count.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Command: $command"
        echo "  Output:"
        cat /tmp/test_output_host_$test_count.log | sed 's/^/    /'
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Change to project directory
cd "$(dirname "$0")/.."

# Test 1: Docker compose file exists
run_test "compose.yaml exists" \
    "test -f compose.yaml"

# Test 2: Dockerfile exists
run_test "Dockerfile exists" \
    "test -f docker/Dockerfile"

# Test 3: Docker compose can build (or image exists)
run_test "Docker image can be built or already exists" \
    "docker compose build > /dev/null 2>&1 || docker images | grep -q 'osm_city_pipeline'"

# Test 4: Docker compose can start container
run_test "Docker compose can start container" \
    "docker compose up -d > /dev/null 2>&1 && sleep 3 && docker compose ps | grep -q 'Up'"

# Test 5: Container is accessible
run_test "Container is accessible" \
    "docker compose exec -T osm_city_pipeline echo 'test' | grep -q 'test'"

# Test 6: Container has required tools
run_test "Container has Python 3" \
    "docker compose exec -T osm_city_pipeline python3 --version | grep -q 'Python'"

# Test 7: Container can run CLI
run_test "Container can run CLI from host" \
    "docker compose exec -T osm_city_pipeline bash -c 'cd /workspace/osm_city_pipeline && PYTHONPATH=/workspace/osm_city_pipeline/src python3 src/osm_city_pipeline/cli.py --help' | grep -q 'OSM City Pipeline'"

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
    echo -e "${GREEN}✓ ALL DOCKER TESTS PASSED${NC}"
    exit 0
fi

