# Dockerfile for ROS 2 Jazzy + Gazebo Harmonic
FROM osrf/ros:jazzy-desktop-full

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy

# Install GIS dependencies and Python tools
# Note: Gazebo Harmonic comes with ros:jazzy-desktop-full base image
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

# Install Python GIS dependencies
# Use --break-system-packages as we're in a container environment
RUN pip3 install --no-cache-dir --break-system-packages \
    pyproj \
    osmium \
    shapely \
    pyyaml

# Initialize rosdep
RUN rosdep update || true

# Set working directory
WORKDIR /workspace/osm_city_pipeline

# Create a user-friendly environment
ENV SHELL=/bin/bash

# Default command
CMD ["/bin/bash"]

