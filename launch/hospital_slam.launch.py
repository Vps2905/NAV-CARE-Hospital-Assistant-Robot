"""Phase 2: SLAM Toolbox only. Keep Phase 1 hospital_sim.launch.py running.

Run in a separate terminal:
  ros2 launch ./launch/hospital_slam.launch.py

This launch does NOT start Gazebo or Nav2 and should NOT be run twice.
"""
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    slam_launch = PathJoinSubstitution([
        FindPackageShare('slam_toolbox'),
        'launch',
        'online_async_launch.py',
    ])
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch),
            launch_arguments={'use_sim_time': 'true'}.items(),
        ),
    ])
