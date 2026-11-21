# Delivery checklist — Medical Analyst Robot

## Phase 1: Hospital environment
- [ ] Show the six separate areas and door clearances in Gazebo.
- [ ] Include 20m x 14m floorplan screenshot, start point, and waypoint chart.
- [ ] Demonstrate that robot and medical furniture do not interpenetrate at initial state.

## Phase 2: Robot and mapping
- [ ] Drive robot manually at safe demonstration speed.
- [ ] Verify /scan, /odom, /tf, /clock; use simulator time for all nodes.
- [ ] Generate a full SLAM map; save map and capture screenshot from RViz2.

## Phase 3: Navigation
- [ ] Configure Nav2 costmaps with correct footprint and safety buffer.
- [ ] Test reception -> general medicine, reception -> orthopedics, reception -> nurse station, reception -> laboratory, reception -> waiting.
- [ ] Test obstacle placed in corridor, stop/replan, no route cases, stop button.
- [ ] Verify robot returns home only with staff authorization.

## Phase 4: Patient interface
- [ ] Ask consent; patient enters a fictional name/age/ID (prototype mode).
- [ ] Integrate suitable SpO2/heart-rate/BP devices or display clearly identified simulated values.
- [ ] Ask reason for visit, transcribe speech, repeat back for correction.
- [ ] Confirm suggested destination with staff or patient.
- [ ] Display and play directions; manual touch and nurse escalation fallback.

## Phase 5: Final demonstration
- [ ] Record at least 5 valid navigation trials to each destination (25 total); log every failed trial too.
- [ ] Record obstacle outcomes, travel time, goal error, collisions/contacts and route completion.
- [ ] Generate a *fictional data* report with time and explicit source/quality of each value.
- [ ] Show successful planned route and one safety/urgent-case stop.
- [ ] Present separate 'implemented', 'demonstrated', and 'future work' sections; no invented accuracy claims.
