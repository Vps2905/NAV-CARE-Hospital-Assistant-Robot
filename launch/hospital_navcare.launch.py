"""Launch the six-room hospital and spawn the NAV CARE model FROM THE URDF.

The original hospital_sim.launch.py is intentionally not modified.
This world contains no old robot, so only one /cmd_vel and /odom source is spawned.
"""
from pathlib import Path
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch_ros.actions import Node

BASE = Path(__file__).resolve().parents[1]
WORLD = BASE / 'worlds' / 'hospital_navcare.sdf'
URDF = BASE / 'models' / 'navcare_assistant' / 'urdf' / 'navcare_assistant.urdf'


def generate_launch_description():
    if not WORLD.is_file():
        raise RuntimeError('First run: python3 scripts/prepare_navcare_world.py')
    if not URDF.is_file():
        raise RuntimeError(f'NAV CARE URDF not found: {URDF}')
    # model://navcare_assistant/meshes/... resolves via this resource path.
    paths = [str(BASE / 'models')]
    inherited = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    if inherited:
        paths.append(inherited)

    return LaunchDescription([
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.pathsep.join(paths)),
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', '-v', '4', str(WORLD)], output='screen',
        ),
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            name='navcare_robot_state_publisher', output='screen',
            parameters=[{'use_sim_time': True, 'robot_description': URDF.read_text()}],
        ),
        Node(
            package='ros_gz_bridge', executable='parameter_bridge',
            name='navcare_gazebo_bridge', output='screen',
            parameters=[{'config_file': str(BASE / 'ros' / 'bridge_navcare.yaml'),
                         'use_sim_time': True}],
        ),
        TimerAction(period=7.0, actions=[
            Node(
                package='ros_gz_sim', executable='create',
                name='navcare_spawn_from_urdf', output='screen',
                arguments=[
                    '-world', 'hospital_demo',
                    '-file', str(URDF),
                    '-name', 'hospital_robot',
                    '-x', '-6.65', '-y', '-3.55', '-z', '0.245', '-Y', '1.57079632679',
                ],
            )
        ]),
    ])
