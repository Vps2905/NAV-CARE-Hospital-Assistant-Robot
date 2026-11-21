#!/usr/bin/env python3
"""Optional ROS2 Nav2 goal client. Requires a configured + active SLAM/Nav2 stack.
Not run by patient_demo.py automatically; staff must authorize movement.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description='Send a destination goal to Nav2')
    parser.add_argument('destination', help='One of the keys in config/locations.json')
    parser.add_argument('--return-home', action='store_true', help='Return to reception after a successful goal')
    args = parser.parse_args()
    loc = json.loads((ROOT / 'config' / 'locations.json').read_text())['destinations']
    if args.destination not in loc:
        parser.error('Unknown destination. Choose: ' + ', '.join(loc))
    try:
        import rclpy
        from geometry_msgs.msg import PoseStamped
        from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
    except ImportError as exc:
        raise SystemExit('ROS2/Nav2 is not available in this Python environment: ' + str(exc))

    rclpy.init()
    navigator = BasicNavigator()
    try:
        print('Waiting for ACTIVE Nav2 servers. Verify SLAM/localization, /map, /scan, /tf, /odom first.')
        navigator.waitUntilNav2Active()

        def goal_for(room: str):
            d = loc[room]
            goal = PoseStamped()
            goal.header.frame_id = 'map'
            goal.header.stamp = navigator.get_clock().now().to_msg()
            goal.pose.position.x = float(d['x'])
            goal.pose.position.y = float(d['y'])
            rad = math.radians(float(d['yaw_deg']))
            goal.pose.orientation.z = math.sin(rad / 2)
            goal.pose.orientation.w = math.cos(rad / 2)
            return goal

        def drive(room: str) -> bool:
            print('Navigation requested ->', loc[room]['label'])
            navigator.goToPose(goal_for(room))
            while not navigator.isTaskComplete():
                # Obstacle avoidance must be provided by the configured Nav2 costmaps / controller.
                # This client does not track whether a person is actually walking behind the robot.
                feedback = navigator.getFeedback()
                if feedback is not None:
                    print('\rNavigating... (staff supervision required)', end='', flush=True)
            print()
            result = navigator.getResult()
            if result == TaskResult.SUCCEEDED:
                print('ARRIVED:', loc[room]['label'])
                return True
            print('Navigation did not succeed:', result, 'Human staff assistance required.')
            return False

        if drive(args.destination) and args.return_home and args.destination != 'reception':
            confirm = input('Staff: area clear and safe to return to reception? [y/N]: ').strip().lower()
            if confirm == 'y':
                drive('reception')
    except KeyboardInterrupt:
        navigator.cancelTask()
        print('\nGoal cancelled by operator.')
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
