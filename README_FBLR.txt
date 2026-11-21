NAV CARE: Simple F/B/L/R Gazebo mapping controller

1. Save this ZIP inside: ~/Documents/hospital robot/
2. Stop teleop_twist_keyboard (Ctrl+C); do NOT stop Gazebo and SLAM.
3. In Terminal:
   cd ~/Documents/"hospital robot"
   unzip -o NAV_CARE_FBLR_Controls.zip -d hospital_robot_starter
   cd hospital_robot_starter
   source /opt/ros/lyrical/setup.bash
   python3 scripts/fblr_control.py

One-key controls (no Enter):
F: forward 0.15m (time-commanded)
B: backward 0.12m (time-commanded)
L: left ~28 degrees (time-commanded)
R: right ~28 degrees (time-commanded)
S or space: stop immediately
Q: stop and quit

Commands last no more than 1.5 seconds, and automatically stop. The robot
can still collide with walls or furniture: this controller does not provide
obstacle avoidance. Use only in Gazebo, not on a physical robot.

Important: Do not run multiple motion controllers simultaneously.
