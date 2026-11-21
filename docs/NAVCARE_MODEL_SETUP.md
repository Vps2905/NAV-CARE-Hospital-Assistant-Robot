# NAV CARE humanoid medical assistant: URDF + Gazebo integration

## Contents

- `models/navcare_assistant/urdf/navcare_assistant.urdf` — editable **URDF source**.
- `models/navcare_assistant/meshes/*.stl` — custom smooth body/head, screen, eyes, grippers.
- `docs/navcare_robot_preview.png` — offline preview of the generated URDF geometry.
- `scripts/start_navcare.sh` — convenience launcher after extraction.
- `launch/hospital_navcare.launch.py` — six-room Gazebo + URDF spawn + ROS bridge + robot_state_publisher.
- `scripts/prepare_navcare_world.py` — creates `worlds/hospital_navcare.sdf`, leaving original world untouched.
- `scripts/validate_navcare_model.py` — checks URDF, URDF->SDF conversion (if Gazebo installed), mesh assets.
- `ros/bridge_navcare.yaml` — `/clock`, `/cmd_vel` (`TwistStamped`), `/odom`, `/scan`, `/tf`, front camera image.

## Starting from the user's existing hospital_robot_starter project

Do **not** start the original `hospital_sim.launch.py` at the same time. Also stop SLAM, Nav2 and the FBLR controller before replacing the old robot.

```bash
cd ~/Documents/"hospital robot"
unzip -o NAV_CARE_URDF_Gazebo_Upgrade.zip -d hospital_robot_starter
cd hospital_robot_starter
source /opt/ros/lyrical/setup.bash
sudo apt install ros-lyrical-robot-state-publisher ros-lyrical-ros-gz
python3 scripts/prepare_navcare_world.py
python3 scripts/validate_navcare_model.py
ros2 launch ./launch/hospital_navcare.launch.py
```

The included `worlds/hospital_navcare.sdf` already contains all six rooms (and no old robot). The Gazebo world starts and, after a short delay, the new URDF model is spawned at reception (`x=-6.65`, `y=-3.55`, `z=0.245`, `yaw=+90°`). The old hospital world and `hospital_sim.launch.py` **remain intact**; the new world has a different filename.

### Confirm motors and sensors

Open another terminal:

```bash
source /opt/ros/lyrical/setup.bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
python3 scripts/check_sim_topics.py --timeout 20
ros2 run tf2_ros tf2_echo base_link laser_frame
```

The expected laser transform is `x=0.335, y=0, z=0.28` relative to `base_link`; Gazebo LiDAR data is on `/scan` and odometry is on `/odom`.

Run a **short** drive check, with Gazebo in view:

```bash
python3 scripts/safe_drive_test.py --go
```

Only after confirming odometry, TF and motion should you restart the separate `hospital_nav2.launch.py` process. The previously diagnosed Global Costmap disconnected-path issue is **not repaired by replacing the robot model**.

### Preview just the robot in RViz2 (optional)

While the new launch is active, open RViz2, set Fixed Frame=`base_link`, add `RobotModel` and set the source to `robot_description`. RViz2 may show a missing mesh if `model://` URIs are not resolved by its renderer, even though Gazebo renders the robot; use Gazebo as the primary 3D preview.

### Model vs. reality

- **Simulated and functional:** DiffDrive motors, wheel odometry, lower navigation LiDAR (`laser_frame`), front RGB camera (low resolution) and ROS TF for fixed links.
- **Visual placeholders:** blue animated-looking eyes (static), chest touchscreen interface, side cameras, top LiDAR cap, pulse oximeter, blood-pressure cuff, curved grippers, shoulder pressure sensors, charging hardware. There is **no** real vital-sign measurement and no animated arms.
- **Collision limitations:** body and wheels have simplified collision shapes; arms and grippers are non-colliding decorative visuals. Do not infer that the physical arm width is protected by Nav2's original 0.37 m robot radius. Re-evaluate robot footprint, dynamic clearance and tipping before any real hardware deployment.

### Technical notes

The root `base_link` frame is spawned 0.245 m above the floor, matching the old Gazebo robot's base link height. The active low navigation LiDAR is moved forward to x=0.335 m (from the earlier x=0.12 m) to avoid the new decorative torso blocking the LiDAR rays. Wheel-centre height is 0.112 m with a radius of 0.105 m, wheel separation is 0.49 m. The `/cmd_vel` bridge still expects ROS `geometry_msgs/msg/TwistStamped` and converts to Gazebo `gz.msgs.Twist`, consistent with the original project. Gazebo's `ros_gz_sim create` spawns the **URDF** directly; no duplicate SDF robot description is needed.

**Troubleshooting:** If `robot_state_publisher` is not found, install the ROS package named above. If the new robot does not spawn, search Terminal 1 for `navcare_spawn_from_urdf` and the first Gazebo error. If the model appears with missing white body/face geometry, check `GZ_SIM_RESOURCE_PATH` points to this project's `models` directory (the launch sets it). If the LiDAR is missing, use `python3 scripts/validate_navcare_model.py` and share its output. If Gazebo is slow on your AMD GPU, comment out the front RGB `sensor` block in the URDF; keep the base LiDAR block.

To revert, stop the new launch and use the existing:

```bash
ros2 launch ./launch/hospital_sim.launch.py
```
