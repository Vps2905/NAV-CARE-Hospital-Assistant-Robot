# NAV CARE — Phase 3: Nav2 with AMCL (simulation only)

This is an add-on to `hospital_robot_starter` for ROS 2 Lyrical + Gazebo Jetty on Ubuntu 26.04.
The clean map is generated from Gazebo *collision geometry*; it is **not** the robot's SLAM map.
It sets AMCL's initial pose to the world spawn at (-6.65, -3.55, 90°).

## First: stop the old stack

Stop `slam_toolbox` (Ctrl+C) and any manual controllers (`fblr_control.py`, `teleop_twist_keyboard`) before starting Nav2. Stop and restart Gazebo too so the robot's physical pose again matches the configured AMCL initial pose.

## Install files

From `~/Documents/"hospital robot"`:

```bash
unzip -o NAV_CARE_Phase3_Nav2_Addon.zip -d hospital_robot_starter
cd hospital_robot_starter
source /opt/ros/lyrical/setup.bash
python3 scripts/prepare_nav2_config.py
```

If packages are missing:

```bash
sudo apt update
sudo apt install ros-lyrical-navigation2 ros-lyrical-nav2-bringup python3-yaml
```

## Launch in separate terminals

**Terminal 1 — freshly restarted Gazebo, with robot at reception:**

```bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
source /opt/ros/lyrical/setup.bash
ros2 launch ./launch/hospital_sim.launch.py
```

**Terminal 2 — Nav2 + AMCL + map server:**

```bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
source /opt/ros/lyrical/setup.bash
ros2 launch ./launch/hospital_nav2.launch.py
```

**Terminal 3 — diagnostics before movement:**

```bash
source /opt/ros/lyrical/setup.bash
ros2 lifecycle get /amcl
ros2 lifecycle get /map_server
ros2 lifecycle get /bt_navigator
ros2 topic echo /map --once --qos-durability transient_local --field info
timeout 15 ros2 topic echo /amcl_pose --once --qos-durability transient_local --field pose.pose.position
# ctrl+c after a successful transform (initial waiting warning is normal):
ros2 run tf2_ros tf2_echo map base_link
```

Expected: lifecycle nodes active; valid 440×320 grid at 0.05m; localization pose approximately (-6.65, -3.55), with x/y varying slightly by AMCL; map->base transform published. Inspect any error logs if not.

**Terminal 4 — RViz:**

```bash
source /opt/ros/lyrical/setup.bash
rviz2 --ros-args -p use_sim_time:=true
```

Inside RViz set Fixed Frame to `map`; add Map (`/map`), LaserScan (`/scan`) and TF. Switch to top-down. OpenGL shader warnings may appear; if the map remains visible they do not necessarily block navigation.

## First supervised short test (only after diagnostics pass)

In Terminal 3:

```bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
python3 scripts/nav2_first_goal.py corridor --go --timeout 90
```

This moves from the initial reception position toward its doorway and corridor. Type `YES` if the route is clear and you are supervising Gazebo. Press Ctrl+C immediately to cancel if needed.

After success, supervised destination test:

```bash
python3 scripts/nav2_first_goal.py general_medicine --go --timeout 180
```

Return to reception only after the prior goal succeeded and staff confirm it is safe:

```bash
python3 scripts/nav2_first_goal.py reception --go --timeout 180
```

## Common issues

- **AMCL is not active:** check Nav2 launch errors and TF `odom -> base_link -> laser_frame`. An AMCL initial pose mismatch can occur if Gazebo has not been freshly restarted at reception.
- **Failed to create a plan:** inspect `/map` and costmaps; do not blindly decrease the robot footprint or inflation radius to force a path.
- **No robot motion:** verify `ros2 topic info /cmd_vel --verbose` says `geometry_msgs/msg/TwistStamped`; confirm the Gazebo bridge is alive, and that collision monitor isn't applying an emergency stop due to scan data.
- **Duplicate map->odom:** stop SLAM Toolbox; only AMCL should publish this transform.
- **Cannot load nav2 params:** re-run `python3 scripts/prepare_nav2_config.py` after sourcing `/opt/ros/lyrical/setup.bash`. The script builds a config from the *installed* Lyrical Nav2 defaults rather than assuming newer defaults.

Important: Static collision geometry and simulated dynamic obstacles have not been validated in actual Nav2 robot traversal. This is only a supervised Gazebo evaluation, not authorization for use around real patients.
