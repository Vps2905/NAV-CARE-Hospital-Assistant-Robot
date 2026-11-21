# NAV CARE — Phase 2: hospital SLAM mapping

Status: **New mapping launch is statically checked but NOT tested in a live ROS/Gazebo runtime**. Phase 1 movement and TF were confirmed by the user's simulation logs (Nov 18, 2026). Use simulated hardware only. Do not launch Nav2 yet.

## Install / prerequisites

Keep **Terminal 1** from Phase 1 running with Gazebo, bridge, and static laser TF:

```bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
source /opt/ros/lyrical/setup.bash
ros2 launch ./launch/hospital_sim.launch.py
```

If this terminal is *already running*, do **not** run it a second time. Check that Gazebo is **playing** (not paused). `ros2 topic list` should contain `/scan`, `/odom`, `/clock`, `/tf`, `/tf_static`.

If installed packages are missing:

```bash
sudo apt update
sudo apt install ros-lyrical-slam-toolbox ros-lyrical-rviz2 ros-lyrical-teleop-twist-keyboard ros-lyrical-nav2-map-server
```

## Terminal 2 — launch SLAM

```bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
source /opt/ros/lyrical/setup.bash
ros2 launch ./launch/hospital_slam.launch.py
```

This starts the official `online_async_launch.py` with `use_sim_time:=true`. SLAM Toolbox subscribes to `/scan` and uses the `odom -> base_link -> laser_frame` transform already established; it publishes `/map` and `map -> odom` as mapping progresses. Do **not** launch another SLAM instance while this one runs.

## Terminal 3 — verify map data

```bash
source /opt/ros/lyrical/setup.bash
ros2 topic list | grep -E '^(/map|/map_metadata|/scan)$'
ros2 topic info /map
ros2 run tf2_ros tf2_echo map odom
```

Press Ctrl+C to stop `tf2_echo` after seeing numerical translations and rotations. If there is a brief `frame does not exist` message at startup, give the mapper a few seconds; a persistent warning needs troubleshooting. Map might initially contain just the reception room.

## Terminal 4 — view map in RViz

```bash
source /opt/ros/lyrical/setup.bash
rviz2 --ros-args -p use_sim_time:=true
```

In RViz: Global Options > **Fixed Frame = map**. Add > **By topic** > `/map` > Map; Add > **By topic** > `/scan` > LaserScan; Add > TF. If the RViz window reports `No transform`, verify SLAM is running, `/clock` is advancing, and `tf2_echo map odom` works.

## Terminal 5 — drive robot cautiously to build map

```bash
source /opt/ros/lyrical/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true -p frame_id:=base_link -p speed:=0.12 -p turn:=0.35 -p repeat_rate:=10.0
```

**Keyboard controls (terminal must be focused):** `i` forward, `,` reverse, `j` turn left, `l` turn right, `k` STOP. Commands may continue until `k` is pressed; always press `k` before changing terminals / exiting. Stop immediately when approaching walls, furniture, people, or doors. This is simulation-only and has no collision safety controller. Start with small movements toward the reception doorway; move along central corridor, then branch into rooms. If the robot rotates in place, stay clear of furniture.

If teleop is interrupted and you suspect it is still moving, run from the project root:

```bash
python3 scripts/safe_drive_test.py --go --linear 0 --angular 0 --seconds 1
```

If that fails, PAUSE Gazebo simulation immediately.

## Save generated map after exploring

```bash
source /opt/ros/lyrical/setup.bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
mkdir -p maps
ros2 run nav2_map_server map_saver_cli -f "$(pwd)/maps/hospital_slam" --ros-args -p use_sim_time:=true
ls -lh maps/hospital_slam.*
```

Look for `hospital_slam.yaml` and a `.pgm` image. These files contain a **SLAM-generated** occupancy map—not an illustrated floor plan. If map_saver_cli reports a timeout, make sure `/map` is publishing and `slam_toolbox` is still running; try the command again after driving.

## Milestone acceptance checklist

- Gazebo remains stable with Phase 1 robot and topics.
- `/map` publishes `nav_msgs/msg/OccupancyGrid` data.
- Transform `map -> odom -> base_link -> laser_frame` resolves.
- RViz2 shows robot laser scan and growing occupancy map.
- After navigating the environment slowly, map can be saved and loaded.

**Next, not yet implemented:** Nav2 costmaps, planner/controller params for the actual robot footprint and TwistStamped commands, collision tests, goals and station return. Patient-facing use requires a separate safety validation and staff supervision.
