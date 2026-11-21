#!/usr/bin/env python3
"""Check simulation /clock, /odom, /scan, and /tf without driving."""
import argparse
import sys
import time


def main():
    parser = argparse.ArgumentParser(description='Check Gazebo topic stream for NAV CARE')
    parser.add_argument('--timeout', type=float, default=12.0)
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 120:
        parser.error('timeout must be in range 1..120 sec')
    try:
        import rclpy
        from rosgraph_msgs.msg import Clock
        from nav_msgs.msg import Odometry
        from sensor_msgs.msg import LaserScan
        from tf2_msgs.msg import TFMessage
    except ImportError as exc:
        print('ROS 2 Python modules missing. Run: source /opt/ros/lyrical/setup.bash')
        print(exc)
        return 2

    rclpy.init()
    node = rclpy.create_node('nav_care_sim_topic_check')
    readings = {}
    subscriptions = []
    specs = [('/clock', Clock), ('/odom', Odometry),
             ('/scan', LaserScan), ('/tf', TFMessage)]
    for topic, msg_type in specs:
        def handle(msg, topic=topic):
            readings[topic] = msg
        subscriptions.append(node.create_subscription(msg_type, topic, handle, 10))
    try:
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline and len(readings) < len(specs):
            rclpy.spin_once(node, timeout_sec=0.2)
        print('\nNAV CARE – ROS 2 simulation topics')
        for topic, _ in specs:
            received = topic in readings
            print(f'{"PASS" if received else "MISSING"}: {topic}')
        if '/scan' in readings:
            scan = readings['/scan']
            print(f'  LiDAR: {len(scan.ranges)} beams, frame={scan.header.frame_id}, '
                  f'range={scan.range_min:.2f}..{scan.range_max:.2f}m')
        if '/odom' in readings:
            o = readings['/odom']
            p = o.pose.pose.position
            print(f'  Odometry: x={p.x:.2f}, y={p.y:.2f}, frame={o.header.frame_id}, '
                  f'child={o.child_frame_id}')
        if len(readings) != len(specs):
            print('Check launch logs, ROS_DOMAIN_ID, bridge.yaml, and Gazebo Play state.')
            return 1
        print('Simulation sensor topics are available. TF frame content still needs validation.')
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
