"""Final model-atlas defects checked against native video frames."""
import json,numpy as np
from pathlib import Path
P=Path('work/rebuild4/architecture');d=json.loads((P/'village_mesh_input.json').read_text());ps=json.loads((P/'village_profiles.json').read_text());g={b['id']:b for b in d['entries']};p={b['id']:b for b in ps['entries']}
b=g['V0329'];q=np.array(b['footprint_world']);a=.61;be=.47;notch=np.array([q[0],q[0]+(q[1]-q[0])*a,q[0]+(q[1]-q[0])*a+(q[3]-q[0])*be,q[0]+(q[3]-q[0])*be]);b['roof_openings_world']=[notch.tolist()];b['top_floor_terrace']=dict(notch_world=notch.tolist(),floor=3,outer_face_voids={'0':[0,a],'3':[1-be,1]},source_image='frame_040.00.jpg',status='source-visible L upper roof and open lower corner terrace; depth inferred from frozen roof plane');b['floor_count']=4
pr=p['V0329'];pr['color']=[.62,.62,.58];pr['style']='plaster';pr['roof_color']=[.82,.83,.78]
for k,f in pr['faces'].items():
 f['openings']=[];f['balconies']=[];f['scaffold']=True;f['color']=[.62,.62,.58];f['annotation_status']='manually reviewed construction facade, frame40, irregular scaffold holes removed'
 if k=='3':
  for y in [.39,.62]:
   for x in [.18,.39]:f['openings'].append(dict(box=[x-.055,y-.075,x+.055,y+.075],kind='empty',inferred=False,source_method='native frame40 observed construction aperture'))
  for floor in [1,2]:f['balconies'].append(dict(x0=.58,x1=.95,floors=[floor],depth=1.15,rail='metal',inferred=True))
 if k=='0':
  for y in [.39,.62]:
   for x in [.25,.61]:f['openings'].append(dict(box=[x-.065,y-.07,x+.065,y+.07],kind='empty',inferred=True,source_method='continuation behind visible construction scaffold'))
g['V0186']['observed_surface_plane']=[0,0,g['V0186']['roof_edge_height']];p['V0186']['roof_color']=[.80,.42,.29];g['V0186']['roof_plane_adjudication']='native frame256 orange L covering is nearly flat; spurious plane gradient rejected'
# Rear gate is visibly open below the small curved tiled roof.
if 'V0111G' in g:
 for k in ['0','2']:
  p['V0111G']['faces'][k].update(openings=[dict(box=[.22,.24,.78,.98],kind='empty',inferred=False,source_method='native frame256 gate passage')],color=[.50,.46,.39],style='plaster')
d['entries']=list(g.values());ps['entries']=list(p.values());(P/'village_mesh_input.json').write_text(json.dumps(d,ensure_ascii=False));(P/'village_profiles.json').write_text(json.dumps(ps,ensure_ascii=False));print('SOURCE CORRECTIONS V0329 V0186 V0111G')
