# NAV CARE – hospital presentation upgrade

This add-on generates a separate SDF and launch file. It does not change your existing world, URDF, map, navigation or dashboard configuration, including the stability and LiDAR fixes previously applied.

From the existing hospital_robot_starter project directory:

    python3 scripts/prepare_realistic_hospital.py
    ros2 launch ./launch/hospital_realistic.launch.py

For animated pedestrians (requires internet access for Gazebo Fuel model assets, or already cached assets):

    python3 scripts/prepare_realistic_hospital.py --people
    ros2 launch ./launch/hospital_realistic.launch.py

Optional dynamic corridor scenario (not yet validated for autonomous missions):

    python3 scripts/prepare_realistic_hospital.py --people --busy-corridor

Stop the old Gazebo, Nav2, RViz and dashboard sessions before restarting. Never run both world launches at once. Launch Nav2 and the dashboard with the same previously working commands after sensors and localization initialize. Keep one goal client active and supervise the simulation.

New decorations: neutral walls and teal bands, signs over doorways, seat backs and cushions, hospital bed mattresses and pillows, computers and lab analyzer detail. Decorations are visual only, over existing furniture or above navigation height. The original collision geometry and map stay unchanged; these visuals may still be seen by GPU LiDAR. The animated people are scripted Gazebo actors, not intelligent agents, and do not have normal physical collisions. Do not treat their detection as verified. Use actor-free mode to recheck baseline navigation before dynamic tests. Actor mesh from the official Gazebo actor tutorial: https://gazebosim.org/docs/harmonic/actors/ . If Fuel fails to load or rendering is slow, generate without --people and restart.

Validation performed: Python compilation, XML generation in both modes, collision geometry equality, unique names, actor loop endpoints/timing and generated lettering files. Gazebo runtime and navigation with decorations/actors have not been tested here. If needed, return to original launch hospital_navcare.launch.py unchanged.
