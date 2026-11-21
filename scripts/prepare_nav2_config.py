#!/usr/bin/env python3
"""Create a Nav2 Lyrical config compatible with the NAV CARE Gazebo starter.

Uses the installed nav2_bringup params as a template, so it tracks the user's
installed Lyrical release. It does not modify the installed ROS files.
Run once after `source /opt/ros/lyrical/setup.bash`.
"""
from __future__ import annotations
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'config' / 'hospital_nav2.yaml'
MAP = ROOT / 'maps' / 'hospital_reference.yaml'


def main():
    try:
        import yaml
        from ament_index_python.packages import get_package_share_directory
    except ImportError as exc:
        print('Missing Python ROS/YAML dependency:', exc)
        print('Run: source /opt/ros/lyrical/setup.bash')
        print('If PyYAML is missing: sudo apt install python3-yaml')
        return 2

    if not MAP.exists() or not MAP.with_suffix('.pgm').exists():
        print('Missing clean reference map in maps/. Extract the clean map ZIP first.')
        return 2

    try:
        nav2_share = Path(get_package_share_directory('nav2_bringup'))
    except Exception as exc:
        print('nav2_bringup not found:', exc)
        print('Try: sudo apt install ros-lyrical-navigation2 ros-lyrical-nav2-bringup')
        return 2

    default_path = nav2_share / 'params' / 'nav2_params.yaml'
    if not default_path.is_file():
        print('Could not locate installed Nav2 configuration:', default_path)
        return 2

    cfg = yaml.safe_load(default_path.read_text())
    for key in ('amcl', 'controller_server', 'local_costmap', 'global_costmap',
                'velocity_smoother', 'collision_monitor', 'planner_server'):
        if key not in cfg:
            print('Unexpected Nav2 config format: missing', key)
            return 2

    def params(name):
        return cfg[name]['ros__parameters']

    amcl = params('amcl')
    amcl.update({
        'base_frame_id': 'base_link',
        'odom_frame_id': 'odom',
        'global_frame_id': 'map',
        'scan_topic': 'scan',
        'set_initial_pose': True,
        'initial_pose': {
            'x': -6.65, 'y': -3.55, 'z': 0.0, 'yaw': math.pi / 2.0,
        },
        'min_particles': 200,
        'max_particles': 1000,
    })

    controller = params('controller_server')
    controller['controller_frequency'] = 10.0
    controller['enable_stamped_cmd_vel'] = True
    # NAV CARE demo robot is differential drive, max 0.35 m/s in SDF.
    if 'FollowPath' in controller and controller['FollowPath'].get('plugin') == 'nav2_mppi_controller::MPPIController':
        follower = controller['FollowPath']
        follower.update({
            'model_dt': 0.1,
            'batch_size': 400,          # reduce CPU load on laptop
            'vx_max': 0.18,
            'vx_min': -0.08,
            'wz_max': 0.50,
            'ax_max': 0.5,
            'ax_min': -0.5,
            'az_max': 1.0,
            'visualize': False,
            'publish_optimal_trajectory': False,
        })
    if 'progress_checker' in controller:
        controller['progress_checker']['required_movement_radius'] = 0.20
        controller['progress_checker']['movement_time_allowance'] = 20.0

    for side in ('local_costmap', 'global_costmap'):
        c = cfg[side][side]['ros__parameters']
        c['robot_base_frame'] = 'base_link'
        # Approximate radius including wheels and corners of the demo chassis.
        # Conservative collision circle; needs physical validation on real hardware.
        c['robot_radius'] = 0.37
        c.pop('filters', None)  # No simulated keepout/speed mask servers configured.
        c['plugins'] = (['obstacle_layer', 'inflation_layer'] if side == 'local_costmap'
                        else ['static_layer', 'obstacle_layer', 'inflation_layer'])
        c.setdefault('obstacle_layer', {})
        c['obstacle_layer'].update({
            'plugin': 'nav2_costmap_2d::ObstacleLayer',
            'enabled': True,
            'observation_sources': 'scan',
            'scan': {
                'topic': 'scan',
                'data_type': 'LaserScan',
                'clearing': True,
                'marking': True,
                'obstacle_max_range': 2.5,
                'obstacle_min_range': 0.0,
                'raytrace_max_range': 3.0,
                'raytrace_min_range': 0.0,
                'max_obstacle_height': 2.0,
            },
        })
        c['inflation_layer'] = {
            'plugin': 'nav2_costmap_2d::InflationLayer',
            'inflation_radius': 0.55,
            'cost_scaling_factor': 4.0,
        }
        if side == 'global_costmap':
            c['track_unknown_space'] = True
            c.setdefault('static_layer', {})
            c['static_layer']['plugin'] = 'nav2_costmap_2d::StaticLayer'
            c['static_layer']['map_subscribe_transient_local'] = True

    planner = params('planner_server')
    if 'GridBased' in planner:
        planner['GridBased'].update({'use_astar': True, 'allow_unknown': False})

    vel = params('velocity_smoother')
    vel.update({
        'enable_stamped_cmd_vel': True,
        'max_velocity': [0.18, 0.0, 0.5],
        'min_velocity': [-0.08, 0.0, -0.5],
        'max_accel': [0.5, 0.0, 1.0],
        'max_decel': [-0.5, 0.0, -1.0],
        'velocity_timeout': 0.5,
    })

    collision = params('collision_monitor')
    collision['base_frame_id'] = 'base_link'
    collision['enable_stamped_cmd_vel'] = True
    collision['enabled'] = True

    if 'behavior_server' in cfg:
        params('behavior_server')['enable_stamped_cmd_vel'] = True
        params('behavior_server')['max_rotational_vel'] = 0.5

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('# Generated from installed nav2_bringup params by NAV CARE.\n'
                   '# Simulation only. Initial pose assumes a FRESH Gazebo restart at reception.\n'
                   + yaml.safe_dump(cfg, sort_keys=False))
    print('OK: Created', OUT)
    print('Map:', MAP)
    print('Initial AMCL pose: x=-6.65 y=-3.55 yaw=90 degrees')
    print('Nav2 velocities capped to 0.18m/s and 0.5rad/s')
    print('Robot radius 0.37m; collision monitor enabled')
    print('Do not run SLAM Toolbox or FBLR keyboard together with Nav2.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
