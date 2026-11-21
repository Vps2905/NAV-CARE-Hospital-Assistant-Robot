NAV CARE stability patch (for the URDF/Gazebo upgrade, not the original blue robot)

The medical-assistant model has two drive wheels but only a rear caster.
A tall wheeled model can pitch forward while accelerating. This patch adds
an almost-frictionless front ground-contact sphere as a stabilizer.

1. Close old Gazebo launch and stop all controllers/Nav2.
2. Extract ZIP INTO existing hospital_robot_starter directory.
3. cd ~/Documents/"hospital robot"/hospital_robot_starter
4. source /opt/ros/lyrical/setup.bash
5. python3 scripts/fix_navcare_stability.py
6. python3 scripts/validate_navcare_model.py
7. ros2 launch ./launch/hospital_navcare.launch.py

In a second terminal:
  source /opt/ros/lyrical/setup.bash
  python3 scripts/check_navcare_tilt.py
  python3 scripts/check_sim_topics.py --timeout 20
  python3 scripts/safe_drive_test.py --go
  python3 scripts/check_navcare_tilt.py

The Gazebo model must remain approximately upright after the drive test.
If it tips, stop driving and send the outputs from check_navcare_tilt.py,
plus a Gazebo screenshot. Avoid Nav2 until stability passes.

NOTE: This is an offline-checked model patch, not a Gazebo physical test.
