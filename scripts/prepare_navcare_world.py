#!/usr/bin/env python3
"""Create a NEW six-room Gazebo world without the original small demo robot.
Does not modify worlds/hospital_demo.sdf.
"""
from pathlib import Path
from xml.etree import ElementTree as ET

root = Path(__file__).resolve().parents[1]
source = root / 'worlds' / 'hospital_demo.sdf'
target = root / 'worlds' / 'hospital_navcare.sdf'
if not source.is_file():
    raise SystemExit(f'Missing original hospital world: {source}')
xml = ET.parse(source)
world = xml.find('./world')
if world is None or world.get('name') != 'hospital_demo':
    raise SystemExit('Expected an SDF world named hospital_demo.')
robot = next((e for e in world.findall('model') if e.get('name') == 'hospital_robot'), None)
if robot is None:
    raise SystemExit('Original hospital_robot model missing. No changes made.')
world.remove(robot)
ET.indent(xml, space='  ')
xml.write(target, encoding='utf-8', xml_declaration=True)
assert not any(m.get('name') == 'hospital_robot' for m in ET.parse(target).findall('.//model'))
print('CREATED:', target)
print('Original unchanged:', source)
print('NEXT: ros2 launch ./launch/hospital_navcare.launch.py')
