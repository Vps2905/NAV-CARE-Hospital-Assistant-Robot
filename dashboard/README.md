# NAV CARE patient assistance dashboard

Local research prototype for the existing ROS 2 Lyrical / Gazebo hospital. No changes to the robot, URDF, map, launch files, or Nav2 YAML. The dashboard uses Python standard library + the existing ROS 2 Python libraries, HTML/CSS/JS and SQLite. No npm, pip or API key needed. All patient data must be fictional; no real medical sensor, diagnosis or clinical triage functionality is provided.

## Install
Save the add-on ZIP in `~/Documents/hospital robot`, then:

```bash
cd ~/Documents/"hospital robot"
unzip -o NAV_CARE_Patient_Dashboard.zip -d hospital_robot_starter
cd hospital_robot_starter
python3 -m unittest discover -s dashboard/tests -v
```

## Dry run (no motion)
```bash
python3 dashboard/server.py --demo
```
Open http://127.0.0.1:8080. Fill example, register, collect simulated vitals, suggest department, confirm and start guidance, confirm handover, return. Dry-run arrival after three seconds changes only the demo state. Voice toggle uses browser speech synthesis if available. Optional dictation depends on browser support and may send audio to the browser speech provider; use fictional speech only. Type instead if unavailable. Dry-run and live data are stored in separate files.

## Live supervised simulation
Keep Gazebo and Nav2 running and robot at reception. No SLAM Toolbox, manual teleop, other action clients or scripts should be controlling the robot. If necessary launch the existing hospital and navigation terminals separately:

```bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
source /opt/ros/lyrical/setup.bash
ros2 launch ./launch/hospital_navcare.launch.py
```

```bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
source /opt/ros/lyrical/setup.bash
ros2 launch ./launch/hospital_nav2.launch.py
```

Do not regenerate corrected Nav2 YAML. Confirm map/localization and the collision monitor are active. Stop dry-run server with Ctrl+C. In a new terminal:

```bash
cd ~/Documents/"hospital robot"/hospital_robot_starter
source /opt/ros/lyrical/setup.bash
python3 dashboard/server.py --live
```
Type `SIMULATION` at the prompt and open http://127.0.0.1:8080. Wait for GAZEBO LIVE / Robot ready. If not ready, the robot health panel lists missing prerequisites. The UI sends a real NavigateToPose action to the Gazebo ROS graph on confirmed guidance; this is not a physical robot controller. Use simulated patients only. Check Gazebo throughout. Do not use other Nav2 goal senders simultaneously. Before guiding ensure robot is at reception. Cancel via dashboard and wait for result; if cancellation is uncertain, stop Nav2, verify the robot is stationary and restart the dashboard only after resolving the issue. Do not rely on browser close or network loss to stop motion. Ctrl+C in the dashboard terminal requests cancellation; verify the robot is stationary. No automatic return before explicit handover/recovery confirmation. An unsigned session is not restored after restart; stored history persists. If Nav2 was moving during a dashboard process crash, stop Nav2 and verify the robot is stationary before restarting.

## Interface details
- Map uses the bundled **static reference map** (440 x 320, 0.05 m/cell, origin -11,-8). Live pose from `map -> base_link`, route overlay from `/plan` if published; may retain last plan during a mission. Not a safety monitor.
- Camera preview from `/navcare/camera/image`, RGB/BGR/RGBA/mono image formats, about 2 fps. Live readiness does not depend on camera; no patient tracking yet.
- Readiness checks `/clock`, `/scan`, `/map`, TF, Nav2 action and lifecycle states, not a formal safety certification. Navigation cancel requested on readiness loss or 240-second wall-clock timeout. Collision monitor remains unchanged.
- Staff must review suggestions. Keyword matching is deliberately simple and does not determine urgency reliably. Recognized example urgent phrases block routine guidance; do not rely on absence of a flag. Lab needs confirmed referral. Unknown/mixed concerns are referred to staff.
- Simulated values are fixed demo values, explicitly not measurements. JSON export is a fictional visit record, not a medical report.
- SQLite files are local under dashboard/data with restricted file permissions. Server binds only to 127.0.0.1, with local session token for POST; not intended for network access or real patient information. Clear history from UI when finished. Not encrypted clinical storage.
- Browser voice is optional; no Whisper/Kokoro installation or local speech recognition integration in this release. No live patient tracking, actual medical devices, glass detection, or ORB-SLAM3 integration.

## Validation
Seven offline Python tests pass (workflow, referral, urgent block, cancellation, reception gate, image encoding, HTTP endpoint). Python compilation and JS syntax check pass. Browser end-to-end rendering not tested here due to browser environment restrictions. Live ROS / Gazebo integration requires local validation.
