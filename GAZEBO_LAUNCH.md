# Gazebo Launch Troubleshooting

## Display/X11 Issues

If you see `qt.qpa.xcb: could not connect to display :0`:

### Option 1: Headless Mode (No GUI)
```bash
source /opt/ros/jazzy/setup.bash
gz sim --headless-rendering -s worlds/bari.sdf
```

### Option 2: Configure X11 Forwarding (WSL2)

On Windows host:
```bash
# Install VcXsrv or X410
# Start X server
# Then in WSL2:
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
```

Then restart container:
```bash
docker compose down
docker compose up -d
```

### Option 3: Use Launch Script
```bash
./scripts/launch_gazebo.sh worlds/bari.sdf
```

## SDF Warnings Fixed

- ✓ Physics gravity structure corrected
- ✓ View controller removed (not needed for SDF 1.11)

## Verify World File

```bash
# Check SDF is valid
python3 -c "import xml.etree.ElementTree as ET; ET.parse('worlds/bari.sdf'); print('SDF valid')"

# Test headless launch
source /opt/ros/jazzy/setup.bash
gz sim --headless-rendering -s worlds/bari.sdf
```
