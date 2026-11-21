#!/usr/bin/env python3
"""Bounded, low-speed demo motion; sends stop even after keyboard interruption.

Do not use on physical motors. Defaults to DRY RUN; --go is required.
"""
import argparse
import sys
import time


def main():
    parser = argparse.ArgumentParser(description='NAV CARE simulated motor smoke test')
    parser.add_argument('--go', action='store_true', help='publish motor commands')
    parser.add_argument('--linear', type=float, default=0.08, help='m/s, max abs 0.12')
    parser.add_argument('--angular', type=float, default=0.0, help='rad/s, max abs 0.4')
    parser.add_argument('--seconds', type=float, default=1.0, help='0.1 to 2.0 sec')
    args = parser.parse_args()
    if not (0.1 <= args.seconds <= 2.0 and abs(args.linear) <= .12 and abs(args.angular) <= .4):
        parser.error('Safety limits: 0.1 <= seconds <= 2; |linear| <= .12; |angular| <= .4')
    print('NAV CARE controlled simulation movement')
    print(f'Velocity: linear={args.linear:.2f}m/s angular={args.angular:.2f}rad/s '
          f'for {args.seconds:.1f}s; expected linear distance <= {abs(args.linear * args.seconds):.2f}m')
    if not args.go:
        print('DRY RUN: no movement. Only use --go after verifying Gazebo and sensor topics.')
        return 0
    try:
        import rclpy
        from geometry_msgs.msg import TwistStamped
    except ImportError as exc:
        print('Missing ROS 2 modules, source /opt/ros/lyrical/setup.bash:', exc)
        return 2
    rclpy.init()
    node = rclpy.create_node('nav_care_safe_drive_test')
    publisher = node.create_publisher(TwistStamped, '/cmd_vel', 10)

    def publish(linear, angular):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.linear.x = linear
        msg.twist.angular.z = angular
        publisher.publish(msg)

    try:
        # Allow ROS graph discovery before sending time-limited commands.
        deadline = time.monotonic() + 4.0
        while publisher.get_subscription_count() == 0 and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        if publisher.get_subscription_count() == 0:
            print('ERROR: no /cmd_vel bridge subscriber. Did you run the launch file?')
            return 1
        print('Sending bounded command. Ctrl+C to abort.')
        until = time.monotonic() + args.seconds
        while time.monotonic() < until:
            publish(args.linear, args.angular)
            time.sleep(0.05)
        print('Done; sending STOP commands.')
        return 0
    except KeyboardInterrupt:
        print('\nInterrupted; sending STOP commands.')
        return 130
    finally:
        # Several zero messages improve odds of reception after interruption.
        for _ in range(12):
            publish(0.0, 0.0)
            time.sleep(0.05)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
