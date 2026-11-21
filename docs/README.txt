NAV CARE HOSPITAL MAP REVIEW

Your sensor-derived hospital_slam_draft.pgm has been preserved unchanged (not bundled).
It shows the main rooms and corridor, but contains extra duplicate/misaligned geometry. Do not substitute it for a verified Nav2 map yet.

The clean hospital_reference.pgm/.yaml in this ZIP are generated from the collision boxes of the original Gazebo hospital_demo.sdf, not from LiDAR or SLAM. This is a simulator-specific known-layout map and must never be represented as a SLAM mapping result or a real-hospital map.

Map resolution: 0.05m/pixel; dimensions: 440 x 320 pixels; origin: (-11,-8,0); extents 22 x 16m.
White is free, black occupied, gray outside building is unknown.

For a Nav2 simulation baseline, save these two reference map files to hospital_robot_starter/maps/ without overwriting your draft. Any Nav2 setup must use map:=...hospital_reference.yaml and a correctly initialized localization system (AMCL / initial pose aligned with Gazebo world pose). Do not run Nav2 while SLAM Toolbox is simultaneously broadcasting map->odom. Check footprint/costmap inflation and simulate low-speed navigation with emergency stop before unsupervised operation.

The maze connectivity check with an illustrative 0.30m inflation radius found a path between reception's original robot start pose and General Medicine, but this is not a real Nav2 traversal result. Dynamic obstacles and hardware safety remain untested.
