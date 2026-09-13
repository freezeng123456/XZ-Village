"""One observed two-storey public building with continuous roof and front corridor."""
import json,numpy as np
from pathlib import Path
from rebuild_v4_orthogonal_fit import orthogonal_outline
P=Path('work/rebuild4/architecture');gd=json.loads((P/'village_mesh_input.json').read_text());pd=json.loads((P/'village_profiles.json').read_text());g={b['id']:b for b in gd['entries']};p={b['id']:b for b in pd['entries']};b=g['V0490'];poly=(np.array([[1337,480],[1800,476],[1830,510],[1355,519]])*2400/2048).tolist();v,fit=orthogonal_outline(poly,'frame_080.00.jpg',9.2);b.update(footprint_world=v[:,:2].tolist(),roof_edge_height=9.2,base_height=1.0,roof_type='flat',floor_count=2,front_face=2,name='Two-storey public building with continuous roof and front corridor',source_image='frame_080.00.jpg',source_ids=['V0490','V0491','V0492'],source_polygon_px=poly,fit=fit,geometry_method='one continuous roof identified in native frame80 and frame86; component divisions merged',base_evidence='dense upward-facing courtyard points frame80 median 0.69 to0.85; floor platform1.0',roof_evidence='west and east multiview flat roof match scores 0.981 and0.979; common fitted roof level9.2, slight roof slope simplified')
pr=p['V0490'];pr.update(color=[.73,.64,.52],roof_color=[.30,.32,.31],glazing_color=[.12,.30,.33],style='plaster',wall_age=.27,roof_age=.55,faces={str(j):dict(openings=[],balconies=[],equipment=[],color=[.73,.64,.52],style='plaster') for j in range(4)})
f=pr['faces']['2'];f.update(public_facade=True,public_crest='both ends',public_gallery=True,annotation_status='manually measured native source frame80 two complete storeys',source_image='frame_080.00.jpg')
def op(x,y,w,h,kind='window'):f['openings'].append(dict(box=[x-w/2,y-h/2,x+w/2,y+h/2],kind=kind,inferred=False,source_method='manual native public-building facade'))
for photo_x in [1375,1395,1445,1465,1507,1526,1647,1666,1709,1728,1776,1795]:
 x=1-(photo_x-1350)/480
 for y in [.25,.75]:op(x,y,.032,.14)
for photo_x in [1357,1412,1430,1490,1551,1621,1675,1690,1738,1753,1815]:
 x=1-(photo_x-1350)/480
 for y in [.28,.78]:op(x,y,.024,.29,'door')
op(1-(1582-1350)/480,.26,.085,.36,'empty');op(1-(1582-1350)/480,.79,.072,.33,'empty')
pr['equipment']=[dict(type='tank',xy=[.54,.24],radius=.60,height=1.4,stand=.85),dict(type='roof_ac',xy=[.29,.28]),dict(type='roof_ac',xy=[.36,.25]),dict(type='roof_ac',xy=[.75,.25])]
for bid in ['V0491','V0492']:g.pop(bid,None);p.pop(bid,None);gd.setdefault('component_adjudications',{})[bid]=dict(status='continuous section of public building V0490',parent_id='V0490',source_image='frame_080.00.jpg')
g['V0472'].update(floor_count=2,base_height=-.80,floor_status='two-storey pink house in native frame90; prior raised DTM base rejected');g['V0471'].update(floor_count=3,base_height=1.30,floor_status='three visible levels in native frame112; earlier local DTM base was roof-biased');g['V0351W1']['floor_count']=1
pd['entries']=list(p.values());gd['entries']=list(g.values());(P/'village_profiles.json').write_text(json.dumps(pd,ensure_ascii=False));(P/'village_mesh_input.json').write_text(json.dumps(gd,ensure_ascii=False));print('UNIFIED PUBLIC FIT',fit['rms_px'],'BODIES',len(g))
