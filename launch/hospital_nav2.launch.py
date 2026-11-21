"""Phase 3 NAV CARE static-map Nav2 bringup. Gazebo must already be running.

Prerequisite: python3 scripts/prepare_nav2_config.py
Start: ros2 launch ./launch/hospital_nav2.launch.py
"""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

ROOT = Path(__file__).resolve().parents[1]


def generate_launch_description():
    bringup_dir = Path(get_package_share_directory('nav2_bringup'))
    nav_params = ROOT / 'config' / 'hospital_nav2.yaml'
    static_map = ROOT / 'maps' / 'hospital_reference.yaml'
    if not nav_params.is_file():
        raise RuntimeError('Missing config/hospital_nav2.yaml; run python3 scripts/prepare_nav2_config.py')
    if not static_map.is_file():
        raise RuntimeError('Missing hospital_reference.yaml; extract the clean map ZIP first')
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(bringup_dir / 'launch' / 'bringup_launch.py')),
            launch_arguments={
                'map': str(static_map),
                'params_file': str(nav_params),
                'slam': 'False',
                'use_localization': 'True',
                'use_sim_time': 'true',
                'autostart': 'True',
                'use_composition': 'False',
                'use_keepout_zones': 'False',
                'use_speed_zones': 'False',
            }.items(),
        ),
    ])
