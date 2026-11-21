# Proposed technical architecture and interaction state machine

## Sensor and interaction split

**Navigation sensors**: simulated 2D LiDAR -> `/scan`, wheel odometry -> `/odom`, TF -> `/tf`. Optional IMU and depth camera in later phases.

**Patient-entered fields**: name, patient ID, age, optional contact info, requested visit reason. These are supplied voluntarily by voice / touch / QR; **robot navigation sensors cannot measure these facts**.

**Medical measurement interfaces (future)**: a compatible pulse-oximeter, automated BP monitor, thermometer. Use device API/Bluetooth/USB with per-reading status; avoid claiming clinical accuracy without validation. `Vital signs` in the starter CLI are **simulated examples**.

## ROS 2 node architecture (target, not all implemented)

```text
          Gazebo Jetty Hospital World
               |   |    |
          scan odom  cmd_vel
               |   |    ^
           ros_gz_bridge
               |   |    |
               v   v    |
       slam_toolbox -> /map   [planned SLAM]
                    |
       Nav2 planner / controller -> /cmd_vel [planned navigation]
                    ^
                    |
       Navigation Escort Controller [starter: app/nav2_escort.py]
                    ^
                    |
   Patient Workflow Manager [starter: app/patient_demo.py]
      /       |         |          \
  kiosk    reason    vital signs   staff safety override
 [planned] [demo]  [demo values]    [planned]
```

## Workflow state diagram

```mermaid
flowchart TD
  A[Robot at reception] --> B[Welcome and obtain consent]
  B --> C[Ask patient for fictional ID / details in demo]
  C --> D[Acquire verified device readings or labeled simulated data]
  D --> E[Ask reason for visit / confirm transcription]
  E --> F{Potential urgent warning?}
  F -- Yes --> G[Stop routing; call human staff immediately]
  F -- No --> H{Reason clear and suitable destination?}
  H -- No --> I[Request staff assistance at nurse station]
  H -- Yes --> J[Propose department: medicine, orthopedics, or referred lab]
  J --> K{Staff/patient confirms?}
  K -- No --> I
  K -- Yes --> L[Nav2 goal request]
  L --> M{Goal reached and staff confirms arrival?}
  M -- No --> N[Stop / replan / human fallback]
  M -- Yes --> O[Announce arrival]
  O --> P[Staff approves return to reception]
  P --> A
```

## Acceptance tests for integration

- Use *fictional* identity and vitals until actual devices and a secure backend are ready.
- Publish only necessary information to authorized staff and log system events, not identifiable patient contents.
- Demonstrate no automatic diagnosis: choose department only under explicit rule and human/patient confirmation.
- Add a nurse-overridden emergency stop (physical emergency stop is mandatory for an actual mobile platform).
- Include localization failure and LiDAR data-loss tests: the robot must stop or enter a safe state.
- Escort requires observing that the patient is actually following or making clear this is **wayfinding**, not continuous patient-following. That capability is not in this starter.
