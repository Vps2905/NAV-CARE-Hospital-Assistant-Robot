import subprocess
import re
import math

result = subprocess.run(
    ["gz", "model", "-m", "hospital_robot", "--pose"],
    capture_output=True,
    text=True,
    timeout=15
)

output = result.stdout + result.stderr

values = re.findall(
    r'^\s*\[\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\]\s*$',
    output,
    re.MULTILINE
)

if len(values) < 2:
    print("Unable to read robot pose:")
    print(output)
    raise SystemExit(1)

x, y, z = map(float, values[-2])
roll, pitch, yaw = map(float, values[-1])

roll = math.degrees(roll)
pitch = math.degrees(pitch)
yaw = math.degrees(yaw)

print("\nNAV CARE ROBOT STABILITY")
print("-------------------------")
print(f"Position: X={x:.3f} Y={y:.3f} Z={z:.3f}")
print(f"Roll:  {roll:.2f} degrees")
print(f"Pitch: {pitch:.2f} degrees")
print(f"Yaw:   {yaw:.2f} degrees")

if abs(roll) < 10 and abs(pitch) < 10:
    print("\nPASS: Robot is upright")
else:
    print("\nWARNING: Robot may be tilted or fallen")
