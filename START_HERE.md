# NAV CARE: Start here — Phase 1 (simulation bringup)

**Goal:** See the six-room hospital in Gazebo Jetty, verify `/scan`, `/odom`, `/tf`, `/clock`, and command a **single 0.08 m/s, 1-second movement** from reception. **No ROS/Gazebo runtime test has been performed in the file creation environment.** This is NOT an autonomous robot yet.

## Step 0 — make sure ROS 2 Lyrical is installed on your Ubuntu 26.04 host

Open Terminal 1:

```bash
source /opt/ros/lyrical/setup.bash
sudo apt update
sudo apt install ros-lyrical-ros-gz ros-lyrical-tf2-ros \
  ros-lyrical-slam-toolbox ros-lyrical-navigation2 ros-lyrical-nav2-bringup
```

If `/opt/ros/lyrical/setup.bash` is missing, first install ROS 2 Lyrical using the official ROS 2 instructions. Do not install an unrelated Gazebo version over the ROS pairing.

## Step 1 — extract ZIP and open project folder

```bash
cd ~/Downloads
unzip -o NAV_CARE_Phase1.zip
cd hospital_robot_starter
source /opt/ros/lyrical/setup.bash
python3 scripts/preflight.py
python3 -m unittest discover -s tests -v
```

If you extracted the ZIP somewhere else, change the `cd` path accordingly.

## Step 2 — launch Gazebo + ROS bridge + laser TF (Terminal 1)

```bash
source /opt/ros/lyrical/setup.bash
cd ~/Downloads/hospital_robot_starter
ros2 launch ./launch/hospital_sim.launch.py
```

You should see a **20 x 14 metre hospital** with reception, waiting area, general medicine, orthopedics, nurse station, and laboratory, plus a blue wheeled robot starting at reception. The Gazebo world has no 3D text signs, so identify rooms using `docs/floor_plan.png`.

If the GUI is blank on AMD Mesa, check the Gazebo errors first; `LIBGL_ALWAYS_SOFTWARE=1` may be tried as a slower graphics troubleshooting option, not a default.

## Step 3 — verify sensors (Terminal 2)

```bash
source /opt/ros/lyrical/setup.bash
cd ~/Downloads/hospital_robot_starter
python3 scripts/check_sim_topics.py --timeout 15
```

Expect `PASS` for `/clock`, `/scan`, `/odom`, `/tf`. If scan is missing, check Ogre2 graphics, the GPU lidar sensor, bridge logs, simulation play state and message types. For frame transforms, you may also run:

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser_frame
```

## Step 4 — small and safe movement (Terminal 2)

First preview command:

```bash
python3 scripts/safe_drive_test.py
```

Then **only after** `/scan` and `/odom` are valid and the robot is stationary in reception:

```bash
python3 scripts/safe_drive_test.py --go
```

The robot should move forward a short distance (nominal 8 cm). The test sends multiple zero-velocity commands at the end and on `Ctrl+C`. This is a **simulated-only smoke test**, not sufficient safety for a real robot. Stop Gazebo if the robot behaves unexpectedly.

## Step 5 — test the patient-routing policy (Terminal 2)

```bash
python3 app/patient_demo.py --example
python3 app/patient_demo.py --reason 'fever'
python3 app/patient_demo.py --reason 'chest pain'
```

It will display the appropriate *suggested* route, or urgent human escalation; **this terminal demo does not move the robot**. Only fictional information and demonstration vital numbers are used.

## Next milestone (after you confirm steps 2–4)

- Connect `slam_toolbox` to `/scan` and `odom -> base_link`.
- Use RViz2 to visualize occupancy map and transform chain.
- Save an actual SLAM map (not just the floor-plan illustration).
- Configure Nav2 for our robot, including footprint, costmaps, recovery, and bounded speed.
- Test *autonomous* reception -> general medicine / orthopedics / laboratory goals, with staff confirmation and obstacle/patient escort safety.

**Important:** No health measurements, patient-following, voice input, or autonomous navigation is implemented in this Phase 1 startup. These are subsequent stages. The existing `docs/ORIGINAL_README.md` explains the full project and existing modules.
