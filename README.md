# NAV CARE – Intelligent Hospital Assistant Robot

## Overview

NAV CARE is a ROS 2-based autonomous hospital assistance
robot designed to support patient registration, department
guidance and hospital navigation.

## Current Release: V1.0

Functional simulation prototype tested in Gazebo.

## Implemented Features

- Custom humanoid-style wheeled robot URDF
- Six-area hospital simulation
- LiDAR and RGB camera integration
- SLAM mapping and AMCL localization
- Nav2 autonomous navigation
- Collision avoidance configuration
- Patient registration dashboard
- Simulated vital-sign monitoring
- Department recommendation with confirmation
- Live robot position and camera streaming
- Dashboard-controlled autonomous navigation
- Patient history management
- Return-to-reception workflow

## Technology Stack

- ROS 2 Lyrical
- Gazebo
- Nav2
- RViz2
- Python
- HTML, CSS and JavaScript
- SQLite
- URDF and SDF

## Hospital Departments

- Reception
- Waiting Area
- General Medicine
- Orthopedics
- Nurse Station
- Laboratory

## Running the Simulation

Prerequisites: ROS 2 Lyrical, Gazebo, ros_gz,
Nav2 and robot_state_publisher.

### Terminal 1: Gazebo

    source /opt/ros/lyrical/setup.bash
    export GZ_PARTITION=navcare_recovery_01
    ros2 launch ./launch/hospital_recovery.launch.py

### Terminal 2: Gazebo GUI

    source /opt/ros/lyrical/setup.bash
    export GZ_PARTITION=navcare_recovery_01
    gz sim -g

### Terminal 3: Nav2

After checking simulation sensor topics:

    source /opt/ros/lyrical/setup.bash
    export GZ_PARTITION=navcare_recovery_01
    ros2 launch ./launch/hospital_nav2.launch.py

### Terminal 4: Patient Dashboard

    source /opt/ros/lyrical/setup.bash
    export GZ_PARTITION=navcare_recovery_01
    python3 dashboard/server.py --live

Enter SIMULATION when prompted.

Dashboard: http://127.0.0.1:8080

## Upcoming Development

- Realistic hospital interiors and animated pedestrians
- Natural voice interaction
- Local conversational AI
- Patient detection and tracking
- Dynamic patient-following supervision
- Medical sensor hardware integration
- Digital patient reports
- Functional robotic arms
- Visual SLAM

## Disclaimer

This project is a simulation prototype for research
and engineering demonstration. Medical measurements
are simulated. It is not a certified medical device
and does not provide medical diagnoses.
