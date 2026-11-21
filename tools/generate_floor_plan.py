#!/usr/bin/env python3
"""Draw an editable-schematic PNG matching config/locations.json."""
import json
from pathlib import Path
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
root = Path(__file__).resolve().parents[1]
locations = json.loads((root/'config/locations.json').read_text())['destinations']
fig, ax = plt.subplots(figsize=(12.8, 8.8))
rooms = [
    ('WAITING AREA',-10,1,-3.325,7,'#c7e6fa'),
    ('GENERAL MEDICINE',-3.325,1,3.325,7,'#d3f2e0'),
    ('ORTHOPEDICS',3.325,1,10,7,'#f7ddc5'),
    ('RECEPTION',-10,-7,-3.325,-1,'#e9d9f3'),
    ('NURSE STATION',-3.325,-7,3.325,-1,'#fbefbd'),
    ('LABORATORY',3.325,-7,10,-1,'#d4e6f7')
]
for name,x1,y1,x2,y2,color in rooms:
    ax.add_patch(Rectangle((x1,y1),x2-x1,y2-y1,facecolor=color,edgecolor='none'))
    label_y = -5.55 if name=='RECEPTION' else ((y1+y2)/2 + 1.5)
    ax.text((x1+x2)/2,label_y,name,ha='center',va='center',weight='bold',fontsize=11,color='#273449')
ax.add_patch(Rectangle((-10,-1),20,2,facecolor='#edf1f3',edgecolor='none'))
ax.text(0,-0.7,'CENTRAL CORRIDOR — 2 m',ha='center',fontsize=11,weight='bold',color='#586679')
# exterior / interior partitions
for y in (-7,7): ax.plot([-10,10],[y,y],color='#435164',lw=7)
for x in (-10,10): ax.plot([x,x],[-7,7],color='#435164',lw=7)
for x in (-3.325,3.325):
    for y1,y2 in [(-7,-1),(1,7)]: ax.plot([x,x],[y1,y2],color='#435164',lw=7)
for y in (-1,1):
    for left,cx,right in [(-10,-6.65,-3.325),(-3.325,0,3.325),(3.325,6.65,10)]:
        ax.plot([left,cx-1.05],[y,y],color='#435164',lw=7)
        ax.plot([cx+1.05,right],[y,y],color='#435164',lw=7)
        ax.plot([cx-1.05,cx+1.05],[y,y],color='#5eb883',lw=2,ls='--')
for key,d in locations.items():
    x,y=d['x'],d['y']
    ax.scatter([x],[y],s=90,zorder=5,color='#217b99',edgecolor='white',lw=1.4)
    ax.text(x,y-.5,f'({x:g}, {y:g})',ha='center',fontsize=8,color='#213d55')
ax.scatter([-6.65],[-3.55],marker='*',s=310,zorder=10,color='#cb4d3a',edgecolors='white')
ax.annotate('ROBOT START',xy=(-6.65,-3.55),xytext=(-9.6,-2.1),
            arrowprops=dict(arrowstyle='->',lw=1.8,color='#b04432'),fontsize=10,fontweight='bold',color='#b04432')
ax.plot([-6.65,-6.65,-6.65,0,0],[-3.55,-1.2,0,0,3.15],ls='--',lw=2.3,color='#258eb6',alpha=.8)
ax.text(-3.6,.47,'Example route — not a measured Nav2 path',fontsize=8,color='#267390',ha='center')
ax.set_xlim(-10.8,10.8); ax.set_ylim(-7.7,7.8); ax.set_aspect('equal')
ax.set_xticks(range(-10,11,2)); ax.set_yticks(range(-7,8,2));ax.grid(alpha=.07)
ax.set_xlabel('X (m) — west to east');ax.set_ylabel('Y (m) — south to north')
ax.set_title('Hospital Robot | 6-Area Simulation Floor Plan',fontsize=18,weight='bold',pad=17)
fig.text(.5,.025,'Development schematic; Gazebo world includes room geometry, furniture and a demo robot but no 3D text signage.',ha='center',fontsize=9)
fig.tight_layout(rect=[0,.045,1,1])
fig.savefig(root/'docs'/'floor_plan.png',dpi=170)
print(root/'docs'/'floor_plan.png')
