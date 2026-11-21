#!/usr/bin/env python3
"""Staff-supervised single Nav2 goal test in the NAV CARE simulated hospital.

Does not start a goal unless --go is supplied. Cancels after timeout.
Assumes Gazebo freshly restarted at reception and AMCL configured to spawn.
Never use with a manual keyboard controller simultaneously.
"""
from __future__ import annotations
import argparse
import math
import time

GOALS = {
    'corridor': (-6.65, 0.0, 90.0),
    'reception': (-6.65, -3.55, 90.0),
    'waiting': (-6.65, 3.15, 90.0),
    'general_medicine': (0.0, 3.15, 90.0),
    'orthopedics': (6.65, 3.15, 90.0),
    'nurse_station': (0.0, -3.15, -90.0),
    'laboratory': (6.65, -3.15, -90.0),
}


def main():
    parser = argparse.ArgumentParser(description='NAV CARE simulated navigation goal')
    parser.add_argument('destination', choices=GOALS)
    parser.add_argument('--go', action='store_true', help='actually send the Nav2 goal')
    parser.add_argument('--timeout', type=float, default=120.0,
                        help='wall-clock seconds to allow before cancellation (20..240)')
    args = parser.parse_args()
    if not 20.0 <= args.timeout <= 240.0:
        parser.error('timeout must be between 20 and 240 seconds')
    x, y, yaw = GOALS[args.destination]
    print(f'SIMULATION ONLY: target {args.destination} x={x} y={y} yaw={yaw} deg')
    if not args.go:
        print('DRY RUN: No motion commanded. Use --go after navigation readiness checks.')
        return 0

    import rclpy
    from geometry_msgs.msg import PoseStamped, TwistStamped
    from nav2_msgs.action import NavigateToPose
    from rclpy.action import ActionClient
    from action_msgs.msg import GoalStatus

    rclpy.init()
    node = rclpy.create_node('navcare_phase3_test_goal')
    node.set_parameters([rclpy.parameter.Parameter('use_sim_time', value=True)])
    client = ActionClient(node, NavigateToPose, 'navigate_to_pose')
    stop_pub = node.create_publisher(TwistStamped, '/cmd_vel', 10)
    handle = None

    def stop():
        msg = TwistStamped()
        msg.header.frame_id = 'base_link'
        msg.header.stamp = node.get_clock().now().to_msg()
        stop_pub.publish(msg)

    def cancel():
        if handle is not None:
            fut = handle.cancel_goal_async()
            rclpy.spin_until_future_complete(node, fut, timeout_sec=3.0)

    try:
        if not client.wait_for_server(timeout_sec=8.0):
            print('ERROR: Nav2 navigate_to_pose server unavailable. Check Nav2 launch logs.')
            return 2
        print('GOAL will move the robot. Confirm clear route and Gazebo ONLY.')
        answer = input('Type YES to start supervised navigation: ').strip()
        if answer != 'YES':
            print('Aborted.')
            return 0
        goal = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = node.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        rad = math.radians(yaw)
        pose.pose.orientation.z = math.sin(rad / 2.0)
        pose.pose.orientation.w = math.cos(rad / 2.0)
        goal.pose = pose
        send_future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, send_future, timeout_sec=10.0)
        if not send_future.done() or not send_future.result():
            print('Goal request timed out.')
            return 2
        handle = send_future.result()
        if not handle.accepted:
            print('Nav2 rejected the goal. Inspect localization/costmaps.')
            return 2
        result_future = handle.get_result_async()
        deadline = time.monotonic() + args.timeout
        print('Goal accepted. Monitor Gazebo, RViz, and surroundings. Ctrl+C to cancel.')
        while rclpy.ok() and time.monotonic() < deadline and not result_future.done():
            rclpy.spin_once(node, timeout_sec=0.2)
        if not result_future.done():
            print('Timeout reached; canceling navigation goal.')
            cancel()
            return 2
        status = result_future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            print('ARRIVED:', args.destination)
            return 0
        print('Navigation unsuccessful. Action status:', status)
        detail = result_future.result().result
        print('Nav2 error_code:', getattr(detail, 'error_code', 'N/A'))
        print('Nav2 error_msg:', getattr(detail, 'error_msg', 'N/A'))
        return 2
    except KeyboardInterrupt:
        print('\nOperator requested cancellation.')
        cancel()
        return 130
    finally:
        # Repeated zero commands to reduce residual motion from an interrupted test.
        for _ in range(8):
            stop()
            time.sleep(0.05)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
