# NAV CARE / Medical Analyst Robot — hospital starter

**Status:** Gazebo world **generated**, XML structurally checked; five offline routing tests **pass**. **NOT tested inside Gazebo, ROS 2, or Nav2** in this workspace. The included Nav2 client only works after you configure and validate a complete navigation stack.

This is a **development starter**, not a production clinical system. Use **fictional patient details only** in the demo. Simulated numbers are not sensor measurements.

## Included

- `worlds/hospital_demo.sdf`: a 20 × 14 m, single-floor hospital with walls, 2.1 m-wide room doorways, six furnished areas, an approximately 2 m wide central corridor, and a demo two-wheel differential-drive robot with simulated 2D LiDAR (Gazebo GPU lidar), odometry and velocity control.
- `config/locations.json`: reception, waiting area, general medicine, orthopedics, nurse station and laboratory target poses.
- `docs/floor_plan.png`: labeled overhead planning diagram and waypoint locations.
- `app/patient_demo.py`: **terminal** registration, fictional vital-sign placeholders, reasons for visit, referral check, human confirmation, urgent case escalation.
- `app/nav2_escort.py`: Nav2 `BasicNavigator` goal sender. Does not run by itself and does not detect a following patient.
- `ros/bridge.yaml`: Gazebo–ROS 2 topic bridge for clock, TwistStamped command, odometry, laser scan and TF.
- `tools/generate_world.py`: source for rebuilding the SDF.
- `tests/test_intake.py`: basic offline routing checks.

## Design / location coordinates

All coordinates are in **metres**. X is west-to-east, Y is south-to-north. The central corridor is `-1 < y < 1`. The robot begins in Reception `(-6.65,-3.55)` facing towards the north door. Doors are approximately 2.1 m clear opening. Interior destinations are around `(x=-6.65,0,6.65; y=±3.15)`. See the diagram and `config/locations.json` for precise poses.

```
 NORTH
 +-------------------+-------------------+-------------------+
 |   WAITING AREA    |  GENERAL MEDICINE |    ORTHOPEDICS    |
 |       (-6.65,3)   |       (0,3)       |       (6.65,3)    |
 +-------  DOOR  ----+------- DOOR  -----+------ DOOR  ------+
 |                       CENTRAL CORRIDOR                     |
 +-------  DOOR  ----+------- DOOR  -----+------ DOOR  ------+
 |    RECEPTION      |   NURSE STATION   |     LABORATORY     |
 |    ROBOT START    |       (0,-3)      |       (6.65,-3)   |
 +-------------------+-------------------+-------------------+
 SOUTH
```

## Milestone A — run the patient-interaction demo (no ROS needed)

From the extracted folder:

```bash
python3 tools/check_assets.py
python3 -m unittest discover -s tests -v
python3 app/patient_demo.py --example
python3 app/patient_demo.py --reason 'fever and cough'
python3 app/patient_demo.py --reason 'chest pain'
python3 app/patient_demo.py
```

The patient demo **does not** move the robot. It intentionally uses a simple conservative keyword router; it is not medical triage or a trained AI model.

## Milestone B — run the 3D hospital + robot in Gazebo Jetty

For **Ubuntu 26.04 / ROS 2 Lyrical**, use the matching **Gazebo Jetty** release. Check available packages on your system before installing.

```bash
source /opt/ros/lyrical/setup.bash
sudo apt update
sudo apt install ros-lyrical-ros-gz ros-lyrical-navigation2 ros-lyrical-nav2-bringup ros-lyrical-slam-toolbox ros-lyrical-tf2-ros
cd /path/to/hospital_robot_starter
gz sim -r -v 4 worlds/hospital_demo.sdf
```

If Gazebo fails to render, inspect the `gz sim -v 4` output and graphics support for Ogre2 / GPU lidar. **A valid XML world is not proof that simulation dynamics, sensor outputs, or graphics work.**

### Bridge and initial movement

In a **second** terminal:

```bash
source /opt/ros/lyrical/setup.bash
cd /path/to/hospital_robot_starter
ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=$(pwd)/ros/bridge.yaml -p use_sim_time:=true
```

In a **third** terminal:

```bash
source /opt/ros/lyrical/setup.bash
ros2 topic list
ros2 topic echo --once /scan
ros2 topic echo --once /odom
```

Test a **short** low-speed drive only after confirming the robot is inside its room and the route is clear. Use `Ctrl-C` to stop continuous publication; publish a zero-velocity command immediately after.

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/TwistStamped '{twist: {linear: {x: 0.10}, angular: {z: 0.0}}}'
# Ctrl-C after about 1 second, then command stop:
ros2 topic pub --once /cmd_vel geometry_msgs/msg/TwistStamped '{twist: {linear: {x: 0.0}, angular: {z: 0.0}}}'
```

Do not leave an unattended robot driving. `TwistStamped` is chosen for the modern Nav2 stack. If your robot firmware or controller uses `Twist`, adapt both Nav2 `enable_stamped_cmd_vel` and bridge type consistently.

## Milestone C — validate TF, SLAM, and navigation

The SDF's diff-drive plugin publishes `odom` and `odom -> base_link` TF. Publish the **static** `base_link -> laser_frame` transform matching the SDF lidar pose. Run in a fourth terminal:

```bash
source /opt/ros/lyrical/setup.bash
ros2 run tf2_ros static_transform_publisher --x 0.12 --y 0 --z 0.28 --roll 0 --pitch 0 --yaw 0 --frame-id base_link --child-frame-id laser_frame
```

Verify:

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser_frame
```

**Next integrate SLAM and Nav2.** The exact Nav2 parameters (`robot_radius`, inflation radius, controller, sensor topics, TF tolerance, recovery behaviors, command topic, safety limits) must be configured for this robot after the Gazebo and TF tests. In the mapping phase you can run:

```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true
```

Drive around the six rooms to construct a 2D occupancy map; inspect `/map`, RViz2, and TF (`map -> odom -> base_link -> laser_frame`). Save a verified map for repeatable navigation. After that, configure Nav2 using the ROS 2 Lyrical `nav2_bringup` package for this model; confirm `NavigateToPose` action is active and the map/pose estimate is valid. This starter **does not include a validated Nav2 params file or one-click SLAM + Nav2 launch**, so auto-escort is not working out of the box.

When the navigation server is correctly running:

```bash
python3 app/nav2_escort.py orthopedics
# After successful supervised trials:
python3 app/nav2_escort.py general_medicine --return-home
```

The waypoint file contains the robot centre's destination pose, **not** a doctor consultation room entrance slot or a guaranteed collision-free route. Check clearance against robot footprint and furnishings. The robot must stop if a person is not following or route becomes unsafe; person-follow detection is **not implemented** here.

## Milestone D — sensors, voice, records (still to implement)

For a real demonstrator, add patient **input** using a touchscreen or voice STT with explicit consent. Name/age/visit reason cannot be obtained reliably by LiDAR, SpO2 or pulse sensors. Connect compatible off-the-shelf devices through supported interfaces: pulse oximeter (SpO2/pulse), automated BP monitor (BP), thermometer if needed. A reader must link each reading to the correct patient and show sensor quality/measurement status. Never fabricate a measurement or describe a demonstration constant as a patient result.

For the speech interface, connect `Speech-to-Text -> confirmed reason -> simple routing policy -> Text-to-Speech`. The path must support a touch/manual fallback and a staff override. Use test data, data minimization, access control, consent, and security by design.

## Suggested acceptance tests for your college demo

1. Hospital world loads and shows six labeled rooms (floor plan; Gazebo geometry itself does not have 3D text signage).
2. Robot starts at reception; doors and central corridor are clear.
3. Robot can be moved slowly, `/scan`, `/odom` and TF are valid.
4. Map is generated by SLAM and the robot navigates to all six waypoints using Nav2.
5. Patient interaction with fictional data routes knee pain to orthopedics, fever to general medicine, and lab only when a referral exists.
6. Unknown symptoms request the nurse; urgent symptoms trigger a human escalation and **do not** start escort.
7. Obstacle tests with stopped paths, recoveries, logged outcomes, and staff override work.
8. Real sensor data, if added, comes from compatible devices, displays unit, quality flag, timestamp and patient match.
9. Only when tested, present route-success percentages, time, localization error, and obstacle outcomes. Do not present simulated examples as experimental results.

## Known limitations

- **SDF not runtime-tested**: Gazebo Jetty is not installed in the file-generation environment.
- **Not end-to-end auto-escort**: a validated Nav2 configuration and obstacle/person safety logic are still required.
- **No real sensor integration** and no digital patient records storage.
- **No functioning microphone, touch UI, TTS, obstacle-aware escorted person tracking, or QR registration**; those are next-stage modules.
- **No healthcare suitability or legal compliance claims**. Use under supervision; medical staff remain responsible for clinical decisions.

## Authoritative starting references

- Gazebo Jetty/ROS 2 installation: https://gazebosim.org/docs/latest/ros_installation/
- ROS–Gazebo bridge: https://gazebosim.org/docs/latest/ros2_integration/
- Nav2 setup: https://ros-navigation.github.io/mkdocs.nav2.org/lyrical/configuration_and_development/first_time_robot_setup_guide/odom/setup_odom/
- Nav2 Python Simple Commander: https://api.nav2.org/nav2-lyrical/html/md_nav2_simple_commander_README.html
