# Dockerfile for ROS 2 Jazzy + Gazebo Harmonic
FROM osrf/ros:jazzy-desktop-full

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy

# Install Gazebo Harmonic
RUN apt-get update && apt-get install -y \
    gazebo-harmonic \
    python3-pip \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

# Initialize rosdep
RUN rosdep update || true

# Set working directory
WORKDIR /workspace/osm_city_pipeline

# Create a user-friendly environment
ENV SHELL=/bin/bash

# Default command
CMD ["/bin/bash"]

