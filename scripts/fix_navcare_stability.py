#!/usr/bin/env python3
"""NAV CARE: add a low-friction FRONT ground support to the existing URDF.

Idempotent, backs up the robot model, preserves the original DiffDrive joints,
LiDAR, camera, and ROS topics. This only changes the simulated contact geometry.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
from shutil import copy2
from datetime import datetime

root_dir = Path(__file__).resolve().parents[1]
model = root_dir / 'models/navcare_assistant/urdf/navcare_assistant.urdf'
if not model.is_file():
    raise SystemExit('ERROR: existing NAV CARE URDF not found: ' + str(model))

tree = ET.parse(model)
robot = tree.getroot()
if robot.tag != 'robot' or robot.get('name') != 'navcare_assistant':
    raise SystemExit('ERROR: unexpected robot description; no change made')

if robot.find("./link[@name='front_stabilizer']") is not None:
    print('Already patched: front_stabilizer exists; no changes made.')
    raise SystemExit(0)

# Check assumptions against the original model before editing.
for name in ('base_link','left_wheel','right_wheel','rear_caster'):
    if robot.find(f"./link[@name='{name}']") is None:
        raise SystemExit(f'ERROR: missing expected link {name}; no changes made')
for name in ('left_wheel_joint','right_wheel_joint'):
    if robot.find(f"./joint[@name='{name}']") is None:
        raise SystemExit(f'ERROR: missing expected joint {name}; no changes made')

backup = model.with_suffix('.urdf.backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
copy2(model, backup)

link = ET.SubElement(robot, 'link', {'name':'front_stabilizer'})
inertial = ET.SubElement(link, 'inertial')
ET.SubElement(inertial,'origin',{'xyz':'0 0 0','rpy':'0 0 0'})
ET.SubElement(inertial,'mass',{'value':'0.15'})
ET.SubElement(inertial,'inertia',{'ixx':'0.00022','iyy':'0.00022','izz':'0.00022',
                                  'ixy':'0','ixz':'0','iyz':'0'})
for kind in ('visual','collision'):
    item = ET.SubElement(link,kind)
    ET.SubElement(item,'origin',{'xyz':'0 0 0','rpy':'0 0 0'})
    ET.SubElement(ET.SubElement(item,'geometry'),'sphere',{'radius':'0.060'})
    if kind == 'visual':
        ET.SubElement(item,'material',{'name':'dark'})

joint = ET.SubElement(robot, 'joint', {'name':'front_stabilizer_fixed','type':'fixed'})
ET.SubElement(joint,'parent', {'link':'base_link'})
ET.SubElement(joint,'child', {'link':'front_stabilizer'})
# Main drive wheels bottom: -0.133 - 0.105 = -0.238 m.
# Front support bottom: -0.175 - 0.060 = -0.235 m (3 mm clearance).
ET.SubElement(joint,'origin',{'xyz':'0.215 0 -0.175','rpy':'0 0 0'})

friction = ET.SubElement(robot,'gazebo',{'reference':'front_stabilizer'})
ET.SubElement(friction,'mu1').text = '0.02'
ET.SubElement(friction,'mu2').text = '0.02'

ET.indent(tree,space='  ')
tree.write(model,encoding='utf-8',xml_declaration=True)
# Check that the patched URDF parses before finishing.
ET.parse(model)
print('OK: Added passive front stabilizer ball to NAV CARE URDF.')
print('Robot URDF:',model)
print('Backup URDF:',backup)
print('Rear caster, drive wheel joints, LiDAR and camera are unchanged.')
print('NEXT: stop the old Gazebo session and relaunch hospital_navcare.launch.py')
