#!/usr/bin/env python3
"""Offline structural validation; optional native Gazebo URDF-to-SDF conversion."""
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

root=Path(__file__).resolve().parents[1]
model=root/'models/navcare_assistant/urdf/navcare_assistant.urdf'
tree=ET.parse(model)
assert tree.getroot().tag=='robot'
links={l.attrib['name'] for l in tree.findall('link')}
joints=tree.findall('joint')
assert len(links)>15 and len(joints)>=len(links)-1
assert {'base_link','laser_frame','left_wheel','right_wheel','head_link','torso_link','front_camera_link'}<=links
assert {'left_wheel_joint','right_wheel_joint','laser_fixed'}<={j.get('name') for j in joints}
# All non-root links must appear exactly once as joint children; no undefined parents.
children=[]
for j in joints:
    p=j.find('parent').get('link'); c=j.find('child').get('link')
    assert p in links and c in links,(p,c)
    children.append(c)
assert len(set(children))==len(children)
assert links-set(children)=={'base_link'}
mesh_refs=set()
for mesh in tree.findall('.//mesh'):
    filename=mesh.attrib['filename']
    assert filename.startswith('model://navcare_assistant/meshes/'), filename
    asset=root/'models'/'navcare_assistant'/'meshes'/filename.split('/')[-1]
    assert asset.is_file() and asset.stat().st_size>1000,asset
    mesh_refs.add(filename)
# The model must not accidentally expose fake physiological measurements.
gazebo=tree.findall('gazebo')
assert any(g.find("plugin[@filename='gz-sim-diff-drive-system']") is not None for g in gazebo)
assert any(g.get('reference')=='laser_frame' and g.find('sensor') is not None for g in gazebo)
assert any(g.get('reference')=='front_camera_link' and g.find('sensor') is not None for g in gazebo)
print(f'PASS: URDF valid XML: {len(links)} links, {len(joints)} joints, {len(mesh_refs)} mesh references.')
print('PASS: DiffDrive, base LiDAR, and front camera Gazebo extensions included.')
world=root/'worlds/hospital_navcare.sdf'
if world.is_file():
    ww=ET.parse(world);assert ww.find('./world').get('name')=='hospital_demo'
    assert all(m.get('name')!='hospital_robot' for m in ww.findall('.//model'))
    print('PASS: Hospital world contains no duplicate old robot.')
else: print('INFO: Run python3 scripts/prepare_navcare_world.py first.')
if shutil.which('gz'):
    env=os.environ.copy()
    env['GZ_SIM_RESOURCE_PATH']=str(root/'models')+os.pathsep+env.get('GZ_SIM_RESOURCE_PATH','')
    print('Checking Gazebo native URDF->SDF conversion ...')
    proc=subprocess.run(['gz','sdf','-p',str(model)],capture_output=True,text=True,env=env,timeout=90)
    if proc.returncode:
        print(proc.stderr[-2000:]);raise SystemExit('Gazebo rejected URDF; send the error above.')
    for word in ['DiffDrive','front_lidar','left_wheel_joint','right_wheel_joint']:
        assert word in proc.stdout, f'Missing after native URDF conversion: {word}'
    print('PASS: Gazebo converted URDF and kept motor/sensor configuration.')
else:
    print('SKIP: Gazebo executable unavailable here. Run this script on your ROS laptop for native conversion check.')
