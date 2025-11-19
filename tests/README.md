# Test Suite

This directory contains comprehensive test suites for the OSM City Pipeline project.

## Test Files

- **test_on_host.sh** - Tests Docker setup and container accessibility (runs on host)
- **test_inside_container.sh** - Tests Phase 1 & 2 functionality inside the container
- **test_phases_1_2.sh** - Comprehensive integration test suite for Phase 1 & 2

## Running Tests

### Run all tests from host:
```bash
# Test Docker setup
./tests/test_on_host.sh

# Test inside container (requires container to be running)
docker compose exec osm_city_pipeline /workspace/osm_city_pipeline/tests/test_inside_container.sh

# Comprehensive integration test
./tests/test_phases_1_2.sh
```

### Run tests from inside container:
```bash
docker compose exec osm_city_pipeline bash
cd /workspace/osm_city_pipeline
./tests/test_inside_container.sh
```

## Test Coverage

### Phase 1 Tests:
- Docker image build
- Container startup and accessibility
- Folder structure
- Required files existence
- CLI basic functionality

### Phase 2 Tests:
- pyproj installation
- GIS projection module
- ENU coordinate conversion
- OSM bounds extraction
- CLI test-projection command
- Deterministic output validation

### Integration Tests:
- Full workflow: OSM -> ENU
- Multiple coordinate projections
- Height component handling
- Module imports together
- Volume mounts
- Container persistence

