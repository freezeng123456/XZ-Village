"""Freeze return-view corrections separately from the original source inventory.
Dimensions are visual estimates; no survey accuracy or automatic multiview solve is claimed.
"""
import json,copy
from pathlib import Path
root=Path.cwd();out=root/'work/buildings/v3';out.mkdir(exist_ok=True)
d=json.loads((root/'work/buildings/v2/inventory.json').read_text());ps=json.loads((root/'work/buildings/v2/profiles.json').read_text());bs={b['id']:b for b in d['buildings']};changes=[]
def note(id,what,confidence='visible feature; dimensions estimated'):
 changes.append(dict(id=id,change=what,evidence_frames=[44,252,256,260,264],confidence=confidence));ps[id]['multiview_review']=True

def face(id,j,xs,color=None,style=None,width=1.3,height=1.6):
 b=bs[id];f=ps[id]['facades'][j];f['windows']=[dict(x=x,z=(floor+.60)/b['floors'],width=width,height=height,kind='window') for floor in range(b['floors']) for x in xs];f['loggias']=[]
 if color:f['color']=color
 if style:f['style']=style
 f['layout_evidence']='Return-view visible opening columns; obstructed lower openings remain estimated.'
def color(id,rgb,style=None,age=None):
 p=ps[id];p['wall_color']=rgb
 if style:p['style']=style
 for f in p['facades']:
  f['color']=rgb
  if style:f['style']=style
  if age is not None:f['age']=age

# Roof outline notches visible from both directions. Continue the notch down
# the wall as an explicit reconstruction assumption, recorded with each plan.
for id,a,b in [('B007',.20,.23),('B008',.18,.30),('B010',.12,.22),('B012',.20,.28)]:
 bs[id]['plan_polygon']=[[0,0],[1-a,0],[1-a,b],[1,b],[1,1],[0,1]]
 bs[id]['plan_evidence']='Orthogonal corner notch visible in roof silhouette; metric notch size and lower continuation estimated.'
 note(id,'Rectangular envelope replaced by orthogonal six-corner plan; roof, slabs and walls share the same notch.')
# Four visible rows on the return facade, maintaining observed roof elevation.
b=bs['B007'];b['floors']=4;b['name']='红楼后方灰色四层住宅';b['base_height']=b['roof_height']-4*3.1
for f in ps['B007']['facades']:
 xs=sorted(set(round(w['x'],4) for w in f['windows']));f['windows']=[dict(x=x,z=(k+.6)/4,width=1.25,height=1.6,kind='window') for k in range(4) for x in xs]
 for log in f.get('loggias',[]):log['floors']=[3]
face('B007',2,[.26,.75],[.71,.72,.68],'ceramic_horizontal',1.55,1.6)
for k in range(4):ps['B007']['facades'][2]['windows'].append(dict(x=.56,z=(k+.63)/4,width=.54,height=.75,kind='window'))
ps['B007']['tanks']=[dict(x=.20,y=.73,height=2.0,radius=.33)]
ps['B007']['ac_windows']=[dict(edge=2,x=x,z=(k+.2)/4) for k in [1,2] for x in [.26,.75]]
note('B007','Four storeys, paired rear windows plus narrow bathroom windows; base elevation adjusted, roof elevation retained.')
# Exposed brick and concrete frame, with genuine empty window apertures.
color('B013',[.59,.47,.38],'brick',.19);ps['B013'].update(unfinished=True,concrete_frame=True,cornice='none',roof_color=[.66,.65,.60],tanks=[]);bs['B013']['name']='灰楼后方三层砖混毛坯房'
for j in range(4):face('B013',j,[.26,.72],width=1.35,height=1.75)
note('B013','Remove finished balconies, glazing and ceramic cladding; expose brickwork, concrete frame and floor slabs.')
face('B008',2,[.24,.75],[.78,.79,.75],'aged_plaster',1.55,1.65);face('B008',3,[.52],[.76,.77,.73],'aged_plaster',.95,1.3)
face('B009',2,[.31,.71],[.76,.77,.71],'aged_plaster',.85,1.2);face('B009',3,[.36],[.75,.76,.70],'aged_plaster',.70,1.1)
face('B010',2,[.52],[.77,.78,.73],'aged_plaster',1.2,1.55);face('B010',3,[.45],[.75,.76,.70],'aged_plaster',.75,1.05)
face('B012',2,[.24,.73],[.78,.79,.75],'aged_plaster',1.4,1.65)
face('B019',2,[],[.78,.79,.74],'aged_plaster');face('B019',3,[.28],[.75,.76,.72],'aged_plaster',.85,1.15)
ps['B019']['facades'][2]['windows']=[dict(x=.38,z=.16,width=.85,height=1.05,kind='window')]
for id in ['B008','B009','B010','B012','B019']:note(id,'Different return-facing wall finish and sparse opening layout; reduce repeated generic windows.')
color('R001',[.60,.49,.40],'ceramic_horizontal',.24);note('R001','Restore muted brown ceramic facade family observed in return view.')
color('R002',[.67,.69,.67],'ceramic',.18);ps['R002']['accent_color']=[.56,.28,.25];note('R002','Gray mosaic wall and muted red roof fascia; roof extension remains uncertain.')
for id,rgb in [('R021',[.80,.81,.77]),('R022',[.79,.79,.72])]:color(id,rgb,'aged_plaster',.25);note(id,'Correct shadow-derived dark albedo to pale wall finish.')
ps['R009']['roof_color']=[.40,.67,.79];ps['R009']['roof_age']=.10;note('R009','Blue waterproof flat roof; retain flat slab rather than corrugated metal.')
ps['R017']['terrace_canopy']=dict(color=[.53,.70,.75],x0=.08,x1=.92,y0=.38,y1=.95,height=1.7);note('R017','Add pale blue metal terrace canopy on visible raised supports; dimensions estimated.')
for id in ['R007','R008']:
 color(id,[.48,.49,.46],'aged_plaster',.4);note(id,'Restore darker old plaster and subdued trim; retain existing separate roof units.')
for id,rgb in [('R010',[.64,.44,.35]),('R013',[.67,.43,.34])]:ps[id]['roof_color']=rgb;note(id,'Restore muted terracotta terrace finish visible in return sequence.')
# Resolve visible face assignment from the return-camera comparison, preserving
# outbound balcony faces. Narrow central apertures are not full-size windows.
face('B007',3,[.24,.76],[.71,.72,.68],'ceramic_horizontal',1.55,1.6)
for k in range(4):ps['B007']['facades'][3]['windows'].append(dict(x=.56,z=(k+.63)/4,width=.54,height=.75,kind='window'))
face('B007',2,[.27,.70],[.71,.72,.68],'ceramic_horizontal',.95,1.25)
ps['B007']['ac_windows']=[dict(edge=3,x=x,z=(k+.2)/4) for k in [1,2] for x in [.24,.76]]
face('B008',3,[.23,.77],[.78,.79,.75],'aged_plaster',1.45,1.55)
for k in range(3):ps['B008']['facades'][3]['windows'].append(dict(x=.51,z=(k+.63)/3,width=.56,height=.70,kind='window'))
face('B008',2,[.27,.70],[.76,.77,.73],'aged_plaster',.9,1.25)
ps['B019']['facades'][3]['windows']=[dict(x=.58,z=(k+.6)/3,width=.88,height=1.1,kind='window') for k in [0,1]]
face('R007',0,[.10,.25,.40,.57,.73,.89],width=.92,height=1.35)
face('R013',0,[.20,.78],width=1.4,height=1.55)
for k in range(3):ps['R013']['facades'][0]['windows'].append(dict(x=.5,z=(k+.6)/3,width=.55,height=.72,kind='window'))
face('R021',3,[],[.80,.81,.77],'aged_plaster');face('R021',0,[],[.80,.81,.77],'aged_plaster')
ps['R021']['facades'][0]['windows']=[dict(x=.27,z=(k+.6)/3,width=.80,height=1.0,kind='window') for k in [0,1]];ps['R021']['no_inferred_door']=True
for id,what in [('B007','Align paired return windows with the visible return-facing wall.'),('B008','Align large paired and small central rear windows with return view.'),('B019','Keep two low openings and a blank upper return wall.'),('R007','Restore six visible upper-row windows on the return facade.'),('R013','Distinguish small central stairwell apertures from large windows.'),('R021','Restore largely blank return wall and two low small openings; suppress unsupported exposed door.')]:note(id,what)
# Global tuning is material rendering, not additional source certainty.
for b in d['buildings']:
 p=ps[b['id']];p['trim_color']=[.67,.66,.60] if b['type']=='gable' else [.77,.78,.74]
 for f in p['facades']:
  f['age']=min(.55,f.get('age',.2))
 p['material_revision']='V3 reduced tile contrast, thinner trim, washed-gray dirt and softer runoff; procedural only.'
(out/'inventory.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));(out/'profiles.json').write_text(json.dumps(ps,ensure_ascii=False,indent=2));(out/'multiview_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
print(len(d['buildings']),len(set(x['id'] for x in changes)),len(changes))
