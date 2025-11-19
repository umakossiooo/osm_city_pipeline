#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: docker run ... <osm_path> [output_dir]" >&2
  exit 64
fi

OSM_PATH="$1"
OUTPUT_DIR="${2:-/data}"
APP_DIR="/app"
SCRIPT_SRC="/data/generate_city.py"

if [[ ! -f "$OSM_PATH" ]]; then
  echo "OSM source '$OSM_PATH' not found" >&2
  exit 65
fi

if [[ ! -f "$SCRIPT_SRC" ]]; then
  echo "generate_city.py must be present in the mounted /data directory" >&2
  exit 66
fi

mkdir -p "$APP_DIR"
cp "$SCRIPT_SRC" "$APP_DIR/generate_city.py"
chmod +x "$APP_DIR/generate_city.py"

# Make sure ROS 2 environment variables are available for downstream tools
if [[ -f "/opt/ros/jazzy/setup.bash" ]]; then
  set +u
  source /opt/ros/jazzy/setup.bash
  set -u
fi

python3 /app/generate_city.py "$OSM_PATH" --output-dir "$OUTPUT_DIR"
