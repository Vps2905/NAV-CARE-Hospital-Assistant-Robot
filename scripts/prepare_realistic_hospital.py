#!/usr/bin/env python3
"""Generate a separate decorative hospital world from the existing working world."""
import argparse, math, re
from pathlib import Path
import xml.etree.ElementTree as E

BASE=Path(__file__).resolve().parents[1]
ASSETS=BASE/'assets/hospital_realism'
SRC=BASE/'worlds/hospital_navcare.sdf'
DST=BASE/'worlds/hospital_realistic.sdf'
MESH='https://fuel.gazebosim.org/1.0/Mingfei/models/actor/tip/files/meshes/walk.dae'

def add(parent, tag, value=None, **attrs):
    el=E.SubElement(parent,tag,attrs)
    if value is not None: el.text=str(value)
    return el

def nums(values): return ' '.join(f'{v:.6g}' for v in values)
WHITE=(.91,.94,.96,1); TEAL=(.10,.40,.44,1); BLUE=(.12,.24,.38,1); DARK=(.08,.12,.16,1)
WOOD=(.68,.49,.31,1); CUSHION=(.20,.49,.58,1); METAL=(.64,.70,.74,1); GREEN=(.22,.48,.32,1)

def material(v,color):
    m=add(v,'material'); add(m,'ambient',nums(color)); add(m,'diffuse',nums(color)); add(m,'specular','.12 .12 .12 1')

def box(link,name,pos,size,color,yaw=0):
    v=add(link,'visual',name=name); add(v,'pose',nums((*pos,0,0,yaw)))
    add(add(add(v,'geometry'),'box'),'size',nums(size)); material(v,color); return v

def mesh(link,name,pos,path,color,yaw=0):
    v=add(link,'visual',name=name); add(v,'pose',nums((*pos,0,0,yaw)))
    add(add(add(v,'geometry'),'mesh'),'uri',path.as_uri()); material(v,color)

def sign(world,name,x,y,z,yaw):
    m=add(world,'model',name='decor_sign_'+name); add(m,'static','true'); add(m,'pose',nums((x,y,z,0,0,yaw))); l=add(m,'link',name='link')
    box(l,'back',(0,0,0),(1.94,.035,.29),BLUE)
    mesh(l,'lettering',(0,-.023,0),ASSETS/(name+'.stl'),WHITE)

def actor(world,name,points,delay=0):
    a=add(world,'actor',name=name); s=add(a,'skin'); add(s,'filename',MESH); add(s,'scale','1.0')
    anim=add(a,'animation',name='walk'); add(anim,'filename',MESH); add(anim,'interpolate_x','true')
    script=add(a,'script'); add(script,'loop','true'); add(script,'delay_start',delay); add(script,'auto_start','true')
    tr=add(script,'trajectory',id='0',type='walk',tension='1')
    t=0.; heading=lambda p,q:math.atan2(q[1]-p[1],q[0]-p[0])
    def wp(p,yaw):
        w=add(tr,'waypoint'); add(w,'time',f'{t:.3f}'); add(w,'pose',nums((*p,1.0,0,0,yaw)))
    first_yaw=heading(points[0],points[1]); wp(points[0],first_yaw)
    for i in range(1,len(points)):
        old_yaw=heading(points[i-1],points[i]); t+=math.dist(points[i-1],points[i])/.65; wp(points[i],old_yaw)
        next_yaw=heading(points[i],points[i+1]) if i+1<len(points) else first_yaw
        t+=.8; wp(points[i],next_yaw)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--people',action='store_true',help='Add animated Gazebo Fuel actors (requires internet/cache)'); p.add_argument('--busy-corridor',action='store_true',help='Add corridor actor; dynamic test only'); a=p.parse_args()
    if a.busy_corridor and not a.people: p.error('--busy-corridor requires --people')
    if not SRC.exists(): raise SystemExit('Missing '+str(SRC)+'; run existing prepare_navcare_world.py first.')
    xml=E.parse(SRC); world=xml.find('world'); assert world is not None and world.get('name')=='hospital_demo'
    models={m.get('name'):m for m in world.findall('model')}
    assert 'hospital_robot' not in models
    # Base collisions and all existing poses are unchanged.
    for n,m in models.items():
        if n.startswith(('outside_','corridor_wall_','north_divider','south_divider')):
            v=m.find('link/visual'); size=tuple(map(float,v.findtext('geometry/box/size').split()))
            mat=v.find('material'); mat.find('ambient').text=nums(WHITE); mat.find('diffuse').text=nums(WHITE)
            x,y,z=size; l=m.find('link')
            # Colored in-wall stripe on both visible faces, no new floor obstruction.
            box(l,'decor_band',(0,0,-.15),(x+.004,y+.004,.13),TEAL)
        if n.startswith('floor_'):
            v=m.find('link/visual'); mat=v.find('material'); col=(.79,.84,.85,1) if n=='floor_corridor' else (.89,.91,.91,1)
            mat.find('ambient').text=nums(col); mat.find('diffuse').text=nums(col)
    for n in ('waiting_bench1','waiting_bench2'):
        l=models[n].find('link'); width=float(l.findtext('visual/geometry/box/size').split()[0]); count=3 if width>2 else 2
        for j in range(count):
            x=(j-(count-1)/2)*width/count
            box(l,f'decor_seat{j}',(x,0,.265),(width/count-.05,.54,.075),CUSHION)
            box(l,f'decor_back{j}',(x,.25,.52),(width/count-.05,.08,.47),CUSHION)
    for n in ('medicine_bed','orthopedics_bed'):
        l=models[n].find('link'); box(l,'decor_mattress',(0,0,.405),(2.18,.79,.12),WHITE); box(l,'decor_pillow',(-.77,0,.52),(.49,.68,.12),(.99,.99,.99,1)); box(l,'decor_blanket',(.4,0,.48),(1.23,.76,.035),CUSHION)
        for x in (-1.10,1.10): box(l,'decor_rail_'+str(x),(x,0,.60),(.045,.79,.35),METAL)
    for n in ('medicine_desk','orthopedics_desk','nurse_counter','reception_desk'):
        l=models[n].find('link'); z=float(l.findtext('visual/geometry/box/size').split()[2])/2
        box(l,'decor_worktop',(0,0,z+.025),(float(l.findtext('visual/geometry/box/size').split()[0]),.72,.05),WOOD)
        box(l,'decor_monitor_stand',(0,0,z+.13),(.10,.14,.19),DARK)
        box(l,'decor_monitor',(0,0,z+.35),(.48,.08,.30),DARK)
        box(l,'decor_display',(0,-.044,z+.35),(.43,.01,.25),(.12,.47,.60,1))
        box(l,'decor_keyboard',(0,-.20,z+.06),(.37,.15,.024),DARK)
    l=models['lab_counter'].find('link')
    box(l,'decor_lab_top',(0,0,.51),(2.6,.73,.06),WHITE)
    for i in range(6): box(l,f'decor_sample_{i}',(-.63+i*.13,0,.66),(.055,.055,.25),(.30,.65,.72,1))
    box(l,'decor_analyzer',(.72,0,.79),(.63,.48,.53),WHITE); box(l,'decor_analyzer_screen',(.72,-.25,.87),(.37,.025,.21),DARK)
    areas=[('waiting',-6.65,1),('medicine',0,1),('orthopedics',6.65,1),('reception',-6.65,-1),('nurse',0,-1),('laboratory',6.65,-1)]
    for name,x,side in areas:
        # Free-standing visual sign suspended above each existing doorway, facing corridor.
        sign(world,name,x,side,2.28,0 if side>0 else math.pi)
    # Unique name for each sign; additional wayfinding at corridor ends not needed.
    if a.people:
        actor(world,'patient_waiting',[(-8.8,3.0),(-8.8,4.6),(-7.8,4.6),(-7.8,3.0),(-8.8,3.0)])
        actor(world,'staff_medicine',[(1.8,2.4),(2.2,3.8),(1.1,4.1),(1.1,2.4),(1.8,2.4)],2)
        actor(world,'staff_laboratory',[(8.3,-2.3),(8.8,-3.8),(7.8,-4.0),(7.8,-2.3),(8.3,-2.3)],4)
        if a.busy_corridor: actor(world,'corridor_visitor',[(4.2,0),(6.65,0),(6.65,2.1),(6.65,0),(4.2,0)],1)
    E.indent(xml,space='  '); xml.write(DST,encoding='utf-8',xml_declaration=True)
    original=(BASE/'launch/hospital_navcare.launch.py').read_text()
    updated,n=re.subn(r"(['\"])hospital_navcare\.sdf\1", "'hospital_realistic.sdf'",original)
    if n!=1: raise SystemExit('Unexpected launch source; no new launch generated.')
    compile(updated,'hospital_realistic.launch.py','exec'); (BASE/'launch/hospital_realistic.launch.py').write_text(updated)
    print('CREATED:',DST,'| animated people:',len(world.findall('actor')))
    print('Original world, URDF, Nav2 and dashboard unchanged.')
    print('ros2 launch ./launch/hospital_realistic.launch.py')

if __name__=='__main__': main()
