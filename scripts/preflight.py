#!/usr/bin/env python3
"""Fast host and asset diagnostics. Requires only Python standard library."""
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def check(name: str, success: bool, suggestion: str = '') -> bool:
    print(f'{"[OK]" if success else "[MISSING]"} {name}')
    if not success and suggestion:
        print(f'          {suggestion}')
    return success


def main() -> int:
    print('=== NAV CARE | PHASE 1 PREFLIGHT ===')
    print('This script does NOT start Gazebo or prove hardware compatibility.\n')
    ok_assets = True
    for path in ['worlds/hospital_demo.sdf', 'ros/bridge.yaml',
                 'config/locations.json', 'launch/hospital_sim.launch.py']:
        ok_assets &= check(path, (BASE / path).is_file())
    try:
        ET.parse(BASE / 'worlds' / 'hospital_demo.sdf')
        check('SDF XML is well formed', True)
    except (ET.ParseError, FileNotFoundError) as err:
        check(f'SDF parse error: {err}', False)
        ok_assets = False
    has_ros = check('ROS 2 CLI', shutil.which('ros2') is not None,
                    'Install ROS 2 Lyrical / source /opt/ros/lyrical/setup.bash')
    has_gz = check('Gazebo CLI', shutil.which('gz') is not None,
                   'Install via ros-lyrical-ros-gz (Gazebo Jetty pairing).')
    if has_ros:
        for pkg in ['ros_gz_bridge', 'tf2_ros', 'slam_toolbox', 'nav2_bringup']:
            try:
                result = subprocess.run(['ros2', 'pkg', 'prefix', pkg],
                                        capture_output=True, text=True, timeout=8)
                check(f'ROS package {pkg}', result.returncode == 0,
                      f'Install ros-lyrical-{pkg.replace("_", "-")} if available.')
            except (subprocess.TimeoutExpired, OSError):
                check(f'ROS package {pkg}', False)
    else:
        print('[INFO] ROS package checks skipped until ROS environment is sourced.')
    print(f'\nROS_DISTRO={os.environ.get("ROS_DISTRO", "not set")}')
    print(f'Python={sys.version.split()[0]}')
    print('Next: source /opt/ros/lyrical/setup.bash; '
          'then ros2 launch ./launch/hospital_sim.launch.py')
    return 0 if ok_assets else 1


if __name__ == '__main__':
    sys.exit(main())
