#!/usr/bin/env bash
# NAV CARE one-command launcher, run from any working directory.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -f /opt/ros/lyrical/setup.bash ]; then
  echo "ROS 2 Lyrical not found at /opt/ros/lyrical/setup.bash" >&2
  exit 1
fi
source /opt/ros/lyrical/setup.bash
if [ ! -f "$ROOT/worlds/hospital_navcare.sdf" ]; then
  python3 "$ROOT/scripts/prepare_navcare_world.py"
fi
cd "$ROOT"
exec ros2 launch ./launch/hospital_navcare.launch.py
