#!/usr/bin/env python3
"""NAV CARE: read-only Nav2 global costmap diagnostic (Gazebo simulation)."""
import math
from collections import Counter, deque

import rclpy
from nav2_msgs.srv import GetCostmap

POINTS = {
    "robot_at_abort": (-6.31, 0.23),
    "corridor_center": (-3.00, 0.00),
    "medicine_corridor": (0.00, 0.00),
    "medicine_door": (0.00, 1.00),
    "medicine_entrance": (0.00, 1.50),
    "general_medicine_goal": (0.00, 3.15),
}


def main():
    rclpy.init()
    node = rclpy.create_node("navcare_global_costmap_check")
    try:
        client = node.create_client(GetCostmap, "/global_costmap/get_costmap")
        if not client.wait_for_service(timeout_sec=8.0):
            print("ERROR: /global_costmap/get_costmap service unavailable.")
            print("Check: ros2 service list | grep costmap")
            return 1
        future = client.call_async(GetCostmap.Request())
        rclpy.spin_until_future_complete(node, future, timeout_sec=20.0)
        if not future.done() or future.result() is None:
            print("ERROR: Costmap service timed out or failed.")
            return 1
        cm = future.result().map
        meta = cm.metadata
        width, height = int(meta.size_x), int(meta.size_y)
        res = float(meta.resolution)
        ox, oy = meta.origin.position.x, meta.origin.position.y
        costs = cm.data
        if width <= 0 or height <= 0 or len(costs) != width * height:
            print("ERROR: Invalid map dimensions / data length.")
            return 1
        print(f"LIVE GLOBAL COSTMAP: {width} x {height}, {res:.3f} m/cell, frame={cm.header.frame_id}")
        print(f"Origin: ({ox:.2f}, {oy:.2f}); raw cells: {len(costs)}")
        counter = Counter(costs)
        print("Cells: free(0)=%d, inflated(1..252)=%d, inscribed(253)=%d, lethal(254)=%d, unknown(255)=%d" % (
            counter[0], sum(v for k,v in counter.items() if 1 <= k <= 252),
            counter[253], counter[254], counter[255]))

        # This hospital reference map has zero yaw; flag unexpected rotation.
        q = meta.origin.orientation
        if abs(q.z) > 0.001 or abs(q.w) < 0.999:
            print("WARNING: Costmap origin is rotated; point lookup below assumes a non-rotated grid.")

        def cell(x, y):
            cx, cy = math.floor((x - ox) / res), math.floor((y - oy) / res)
            if 0 <= cx < width and 0 <= cy < height:
                return cx, cy
            return None
        def index(p):
            return p[1] * width + p[0]
        def classify(val):
            if val == 255: return "UNKNOWN"
            if val == 254: return "LETHAL OBSTACLE"
            if val == 253: return "INSCRIBED / BLOCKED"
            if val == 0: return "FREE"
            return "INFLATED COST"

        for name, (x,y) in POINTS.items():
            p = cell(x,y)
            if p is None:
                print(f"{name:22} ({x:.2f},{y:.2f}): OUTSIDE COSTMAP")
            else:
                v = int(costs[index(p)])
                print(f"{name:22} ({x:.2f},{y:.2f}): cost={v:3d}, {classify(v)}")

        start = cell(*POINTS["robot_at_abort"])
        target = cell(*POINTS["general_medicine_goal"])
        if not start or not target:
            print("PATH TEST: Start or goal lies outside map.")
            return 0
        if int(costs[index(start)]) >= 253 or int(costs[index(target)]) >= 253:
            print("PATH TEST: Start or goal blocked in LIVE global costmap.")
            return 0
        # Conservative 4-neighbor reachability test: diagnostics only, not Nav2 planning.
        visited = bytearray(width * height)
        todo = deque([start])
        visited[index(start)] = 1
        found = False
        while todo:
            x, y = todo.popleft()
            if (x,y) == target:
                found = True
                break
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx,ny = x+dx,y+dy
                if 0 <= nx < width and 0 <= ny < height:
                    ni = ny * width + nx
                    if not visited[ni] and int(costs[ni]) < 253:
                        visited[ni] = 1
                        todo.append((nx,ny))
        if found:
            print("PATH TEST: Start and goal CONNECTED through non-blocked cells in live costmap.")
            print("If Nav2 still rejects it, inspect planner configuration and refreshed robot pose.")
        else:
            print("PATH TEST: Start and goal DISCONNECTED in live global costmap.")
            print("Inspect obstacle/inflation layers and map alignment before trying another goal.")
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
