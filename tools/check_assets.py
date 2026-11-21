#!/usr/bin/env python3
"""Offline schema/asset sanity checks; not a replacement for running Gazebo/Nav2."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
root = Path(__file__).resolve().parents[1]
world = ET.parse(root/'worlds/hospital_demo.sdf')
assert world.getroot().tag == 'sdf'
models = {m.attrib['name'] for m in world.findall('.//model')}
assert 'hospital_robot' in models
for room in ('reception','waiting','general_medicine','orthopedics','nurse_station','laboratory'):
    assert f'floor_{room}' in models
locations = json.loads((root/'config/locations.json').read_text())
for name, loc in locations['destinations'].items():
    assert -10 < loc['x'] < 10 and -7 < loc['y'] < 7, name
    assert 'yaw_deg' in loc
print('PASS: valid SDF XML, six room floors, drive robot, destination JSON')
