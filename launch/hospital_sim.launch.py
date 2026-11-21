"""Bring up the hospital world, ROS-Gazebo bridge, and laser static TF.

Run with:
  ros2 launch ./launch/hospital_sim.launch.py

This is a simulated robot only; Nav2 is not launched here.
"""
from pathlib import Path
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

BASE = Path(__file__).resolve().parents[1]


def generate_launch_description():
    return LaunchDescription([
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', '-v', '4', str(BASE / 'worlds' / 'hospital_demo.sdf')],
            output='screen',
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='hospital_gazebo_bridge',
            output='screen',
            parameters=[{
                'config_file': str(BASE / 'ros' / 'bridge.yaml'),
                'use_sim_time': True,
            }],
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='laser_static_tf',
            output='screen',
            arguments=[
                '--x', '0.12', '--y', '0.0', '--z', '0.28',
                '--roll', '0', '--pitch', '0', '--yaw', '0',
                '--frame-id', 'base_link', '--child-frame-id', 'laser_frame',
            ],
            parameters=[{'use_sim_time': True}],
        ),
    ])
