#!/usr/bin/env python3
"""Generate an editable six-room hospital world + demo differential drive robot SDF.
All geometry is in metres. World extent: x -10..10; y -7..7.
"""
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
WALL_COLOR = '0.87 0.9 0.94 1'
ROOM_COLORS = {
    'waiting': '0.81 0.91 0.98 1',
    'general_medicine': '0.83 0.96 0.87 1',
    'orthopedics': '0.96 0.89 0.82 1',
    'reception': '0.93 0.85 0.96 1',
    'nurse_station': '0.98 0.94 0.80 1',
    'laboratory': '0.85 0.91 0.97 1',
    'corridor': '0.94 0.96 0.97 1'
}
parts = []

def box(name, x, y, z, sx, sy, sz, color, collidable=True):
    def geom(tag):
        return f'<{tag} name="{tag}"><geometry><box><size>{sx} {sy} {sz}</size></box></geometry></{tag}>'
    collision = geom('collision') if collidable else ''
    return f'''<model name="{escape(name)}"><static>true</static><pose>{x} {y} {z} 0 0 0</pose>
      <link name="link">{collision}
        <visual name="appearance"><geometry><box><size>{sx} {sy} {sz}</size></box></geometry>
          <material><ambient>{color}</ambient><diffuse>{color}</diffuse></material>
        </visual>
      </link>
    </model>'''

# Floor tiles, 3 rooms north, 3 rooms south, with a central 2m-wide corridor.
centers = [-6.65, 0, 6.65]
rooms = [('waiting',-6.65,4), ('general_medicine',0,4), ('orthopedics',6.65,4),
         ('reception',-6.65,-4), ('nurse_station',0,-4), ('laboratory',6.65,-4)]
for name,x,y in rooms:
    parts.append(box(f'floor_{name}', x,y,0.004,6.65,6,0.008,ROOM_COLORS[name],False))
parts.append(box('floor_corridor',0,0,0.004,20,2,0.008,ROOM_COLORS['corridor'],False))
# Walls: all 2.6m high, 12cm thick. Openings of 2.1m width in central walls.
for name,x,y,sx,sy in [
    ('outside_north',0,7,20,.12),('outside_south',0,-7,20,.12),
    ('outside_west',-10,0,.12,14),('outside_east',10,0,.12,14),
    ('north_divider1',-3.325,4,.12,6),('north_divider2',3.325,4,.12,6),
    ('south_divider1',-3.325,-4,.12,6),('south_divider2',3.325,-4,.12,6)
]:
    parts.append(box(name,x,y,1.3,sx,sy,2.6,WALL_COLOR))
# North and south sides of corridor. Each room has a central 2.1m door opening.
for north,y in [(True,1),(False,-1)]:
    for j,cx in enumerate(centers):
        left,right = ([-10,-3.325,3.325][j],[-3.325,3.325,10][j])
        for k,(edge_a,edge_b) in enumerate(((left,cx-1.05),(cx+1.05,right))):
            if edge_b - edge_a > 0:
                parts.append(box(f'corridor_wall_{"N" if north else "S"}_{j}_{k}',
                                 round((edge_a+edge_b)/2,4),y,1.3,
                                 round(edge_b-edge_a,4),.12,2.6,WALL_COLOR))
# Furniture only in interiors; generous door clearance; colors suggest room function.
items = [
    ('reception_desk',-8.0,-5.3,0.47,2.5,.75,.94,'0.49 0.34 0.68 1'),
    ('registration_kiosk',-8.0,-4.65,1.15,.65,.15,.6,'0.16 0.29 0.36 1'),
    ('waiting_bench1',-8.0,5.7,.24,2.5,.65,.48,'0.29 0.48 0.64 1'),
    ('waiting_bench2',-4.65,5.7,.24,1.6,.65,.48,'0.29 0.48 0.64 1'),
    ('medicine_bed',-1.55,5.4,.36,2.3,.85,.72,'0.38 0.64 0.48 1'),
    ('medicine_desk',1.75,5.7,.42,1.65,.75,.84,'0.5 0.62 0.55 1'),
    ('orthopedics_bed',5.0,5.4,.36,2.35,.85,.72,'0.7 0.53 0.34 1'),
    ('orthopedics_desk',8.45,5.7,.42,1.6,.75,.84,'0.65 0.53 0.44 1'),
    ('nurse_counter',-1.35,-5.6,.45,2.8,.75,.9,'0.76 0.6 0.29 1'),
    ('lab_counter',5.0,-5.6,.48,2.6,.75,.96,'0.36 0.59 0.75 1'),
    ('lab_equipment',8.5,-5.3,.6,.85,.85,1.2,'0.24 0.4 0.55 1')
]
for item in items:
    parts.append(box(*item))

robot = '''
<!-- Minimal demo drive robot. This is a starting model, not a certified healthcare robot. -->
<model name="hospital_robot">
  <pose>-6.65 -3.55 0 0 0 1.570796</pose>
  <link name="base_link">
    <pose>0 0 0.245 0 0 0</pose>
    <inertial><mass>5</mass><inertia><ixx>0.12</ixx><iyy>0.12</iyy><izz>0.18</izz></inertia></inertial>
    <collision name="base_collision"><geometry><box><size>0.47 0.40 0.25</size></box></geometry></collision>
    <visual name="base_visual"><geometry><box><size>0.47 0.40 0.25</size></box></geometry>
      <material><ambient>0.22 0.65 0.79 1</ambient><diffuse>0.22 0.65 0.79 1</diffuse></material></visual>
    <sensor name="front_lidar" type="gpu_lidar">
      <pose>0.12 0 0.28 0 0 0</pose>
      <always_on>1</always_on><update_rate>10</update_rate><topic>/scan</topic>
      <gz_frame_id>laser_frame</gz_frame_id>
      <lidar><scan><horizontal><samples>360</samples><resolution>1</resolution><min_angle>-3.14159</min_angle><max_angle>3.14159</max_angle></horizontal></scan>
        <range><min>0.12</min><max>8.0</max><resolution>0.01</resolution></range></lidar>
    </sensor>
  </link>
  <link name="left_wheel">
    <pose>0 0.245 0.112 -1.570796 0 0</pose>
    <inertial><mass>0.3</mass><inertia><ixx>0.002</ixx><iyy>0.002</iyy><izz>0.001</izz></inertia></inertial>
    <collision name="wheel_collision"><geometry><cylinder><radius>0.105</radius><length>0.055</length></cylinder></geometry></collision>
    <visual name="wheel_visual"><geometry><cylinder><radius>0.105</radius><length>0.055</length></cylinder></geometry>
      <material><ambient>0.12 0.14 0.16 1</ambient><diffuse>0.12 0.14 0.16 1</diffuse></material></visual>
  </link>
  <link name="right_wheel">
    <pose>0 -0.245 0.112 -1.570796 0 0</pose>
    <inertial><mass>0.3</mass><inertia><ixx>0.002</ixx><iyy>0.002</iyy><izz>0.001</izz></inertia></inertial>
    <collision name="wheel_collision"><geometry><cylinder><radius>0.105</radius><length>0.055</length></cylinder></geometry></collision>
    <visual name="wheel_visual"><geometry><cylinder><radius>0.105</radius><length>0.055</length></cylinder></geometry>
      <material><ambient>0.12 0.14 0.16 1</ambient><diffuse>0.12 0.14 0.16 1</diffuse></material></visual>
  </link>
  <link name="rear_caster">
    <pose>-0.21 0 0.073 0 0 0</pose>
    <inertial><mass>0.1</mass><inertia><ixx>0.0005</ixx><iyy>0.0005</iyy><izz>0.0005</izz></inertia></inertial>
    <collision name="caster_collision"><geometry><sphere><radius>0.062</radius></sphere></geometry></collision>
    <visual name="caster_visual"><geometry><sphere><radius>0.062</radius></sphere></geometry></visual>
  </link>
  <joint name="left_wheel_joint" type="revolute"><parent>base_link</parent><child>left_wheel</child>
    <axis><xyz>0 0 1</xyz><limit><lower>-1e16</lower><upper>1e16</upper><effort>8</effort><velocity>20</velocity></limit></axis></joint>
  <joint name="right_wheel_joint" type="revolute"><parent>base_link</parent><child>right_wheel</child>
    <axis><xyz>0 0 1</xyz><limit><lower>-1e16</lower><upper>1e16</upper><effort>8</effort><velocity>20</velocity></limit></axis></joint>
  <joint name="caster_joint" type="ball"><parent>base_link</parent><child>rear_caster</child></joint>
  <plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
    <left_joint>left_wheel_joint</left_joint><right_joint>right_wheel_joint</right_joint>
    <wheel_separation>0.49</wheel_separation><wheel_radius>0.105</wheel_radius>
    <topic>/cmd_vel</topic><odom_topic>/odom</odom_topic><tf_topic>/tf</tf_topic>
    <frame_id>odom</frame_id><child_frame_id>base_link</child_frame_id>
    <odom_publish_frequency>30</odom_publish_frequency>
    <max_linear_velocity>0.35</max_linear_velocity><max_angular_velocity>0.75</max_angular_velocity>
  </plugin>
</model>
'''

world = f'''<?xml version="1.0" encoding="utf-8"?>
<sdf version="1.10">
  <world name="hospital_demo">
    <physics name="default_physics" type="ignored"><max_step_size>0.001</max_step_size><real_time_factor>1</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <scene><ambient>0.8 0.8 0.8 1</ambient><background>0.93 0.96 0.99 1</background><shadows>false</shadows></scene>
    <light name="ceiling_light" type="directional"><pose>0 0 10 0 0 0</pose><diffuse>0.85 0.85 0.85 1</diffuse><specular>0.1 0.1 0.1 1</specular>
      <direction>-0.4 -0.4 -1</direction></light>
    <model name="ground"><static>true</static><link name="ground_link">
      <collision name="floor_collision"><geometry><box><size>30 25 0.1</size></box></geometry><pose>0 0 -0.05 0 0 0</pose></collision>
      <visual name="floor_visual"><geometry><box><size>30 25 0.1</size></box></geometry><pose>0 0 -0.05 0 0 0</pose>
        <material><ambient>0.95 0.95 0.95 1</ambient><diffuse>0.95 0.95 0.95 1</diffuse></material></visual></link></model>
    {''.join(parts)}
    {robot}
  </world>
</sdf>
'''
out = ROOT/'worlds'/'hospital_demo.sdf'
out.write_text(world)
print('Generated',out,'with',len(parts),'static entities')
