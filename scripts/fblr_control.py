#!/usr/bin/env python3
"""NAV CARE Gazebo-only single-key control: f/b/l/r/s/q.

Publishes geometry_msgs/TwistStamped to /cmd_vel, consistent with Phase 1 bridge.
Each command has a short timeout. Requires a real interactive terminal.
Never run alongside teleop_twist_keyboard or autonomous Nav2 controllers.
Not intended for a physical robot.
"""

import select
import sys
import termios
import time
import tty


# Key: (linear m/s, angular rad/s, duration sec, description)
MOVES = {
    'f': (0.20, 0.00, 1.0, 'FORWARD 20 cm'),
    'b': (-0.15, 0.00, 1.0, 'BACKWARD 15 cm'),
    'l': (0.00, 0.60, 1.0, 'LEFT ~34 degrees'),
    'r': (0.00, -0.60, 1.0, 'RIGHT ~34 degrees'),
}


def main():
    if not sys.stdin.isatty():
        print('ERROR: Start this script from an interactive terminal.')
        return 2
    try:
        import rclpy
        from geometry_msgs.msg import TwistStamped
    except ImportError as error:
        print('ERROR: ROS 2 is unavailable. Run: source /opt/ros/lyrical/setup.bash')
        print(error)
        return 2

    rclpy.init()
    node = rclpy.create_node('nav_care_fblr_keyboard')
    pub = node.create_publisher(TwistStamped, '/cmd_vel', 10)

    def send(linear=0.0, angular=0.0):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.linear.x = float(linear)
        msg.twist.angular.z = float(angular)
        pub.publish(msg)

    original_tty = None
    try:
        print('Waiting for Gazebo /cmd_vel bridge...', flush=True)
        discover_deadline = time.monotonic() + 5.0
        while pub.get_subscription_count() == 0 and time.monotonic() < discover_deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        if pub.get_subscription_count() == 0:
            print('ERROR: No /cmd_vel subscriber. Launch hospital_sim.launch.py first.')
            return 1

        original_tty = termios.tcgetattr(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        print('\nNAV CARE – SIMPLE MAPPING CONTROLS (SIMULATION ONLY)')
        print('  F = forward ~15 cm     B = backward ~12 cm')
        print('  L = turn left ~28°     R = turn right ~28°')
        print('  S or SPACE = STOP      Q = quit')
        print('No Enter needed. Every press stops automatically. Keep this terminal focused.\n', flush=True)

        linear = angular = 0.0
        stop_at = 0.0
        while rclpy.ok():
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if ready:
                key = sys.stdin.read(1).lower()
                if key in MOVES:
                    linear, angular, duration, label = MOVES[key]
                    stop_at = time.monotonic() + duration
                    print(label, flush=True)
                elif key in ('s', ' '):
                    linear = angular = 0.0
                    stop_at = 0.0
                    print('STOP', flush=True)
                elif key == 'q':
                    print('Quit – stopping robot.', flush=True)
                    break
            if stop_at and time.monotonic() >= stop_at:
                linear = angular = 0.0
                stop_at = 0.0
                print('Auto-stop', flush=True)
            send(linear, angular)
        return 0
    except KeyboardInterrupt:
        print('\nCtrl+C – stopping robot.', flush=True)
        return 130
    finally:
        # Send multiple stop messages and restore terminal even on exceptions.
        try:
            for _ in range(12):
                send()
                time.sleep(0.05)
        finally:
            if original_tty is not None:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, original_tty)
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
