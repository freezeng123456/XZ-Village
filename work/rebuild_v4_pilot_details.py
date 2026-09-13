"""Explicit low wings, rooftop fixtures and open roof aperture from source frame 44."""
import json,numpy as np,copy
from rebuild_v4_arch_geometry import *
from rebuild_v4_orthogonal_fit import orthogonal_outline
P=OUT;d=json.loads((P/'pilot_mesh_input.json').read_text());profiles=json.loads((P/'pilot_profiles.json').read_text());bs={b['id']:b for b in d['entries']};ps={p['id']:p for p in profiles['entries']}
for bid,parent,poly,z,points in [('P003W1','P003',[[655,709],[690,700],[713,703],[713,732],[655,728]],9.52,89),('P006W1','P006',[[862,646],[891,616],[949,623],[925,656]],10.30,2571)]:
 q,fit=orthogonal_outline(poly,'frame_044.00.jpg',z);b=copy.deepcopy(bs[parent]);b.update(id=bid,name='左侧两层砖混附房' if parent=='P003' else '白色住宅两层临街附楼',parent_id=parent,roof_type='flat',floor_count=2,footprint_world=q[:,:2].tolist(),roof_edge_height=z,observed_roof_surface_height=z-.25,roof_polygon_px=poly,dense_surface_points=points,fit=fit,roof_height_status='89 dense points median 9.38; sparse up-normal support' if parent=='P003' else 'source sparse roof z 9.68..10.13 and dense upper surface support');bs[bid]=b;d['entries']=[x for x in d['entries'] if x['id']!=bid]+[b];p=copy.deepcopy(ps[parent]);p['id']=bid;p['faces']={str(j):dict(openings=[],balconies=[],equipment=[],color=p['color'],style=p['style']) for j in range(len(q))};p['equipment']=[];p['roof_patches']=[]
 if parent=='P003':
  for f in p['faces'].values():f['concrete_frame']=True
  p['faces']['4']['openings']=[dict(box=[.22,.21,.43,.56],kind='empty',inferred=False,source='frame44 visible masonry opening')]
 else:
  for f in [0,1,2,3]:p['faces'][str(f)]['openings']=[dict(box=[.23,.14,.65,.36],kind='window',inferred=f!=0,source='source broad frontage glazing; concealed continuation inferred')]
  p['faces']['0']['balconies']=[dict(x0=0,x1=1,floors=[1],depth=.9,rail='stone',evidence='source frontage railing')]
 profiles['entries']=[x for x in profiles['entries'] if x['id']!=bid]+[p];ps[bid]=p
# The roof contains a genuine opening with returns. It is not a dark painted patch.
b=bs['P010'];q,_=orthogonal_outline([[1065,742],[1078,715],[1121,718],[1110,743]],'frame_044.00.jpg',b['roof_edge_height']-.30);b['roof_openings_world']=[q[:,:2].tolist()];b['roof_opening_source']='frame_044.00.jpg interior aperture corners visually reviewed'
# P008 newly rectified; quiet west side and balconies on the opposite side.
p=ps['P008'];p['color']=[.70,.78,.73]
for f in p['faces'].values():f['color']=p['color']
def op(face,box,inferred=False):p['faces'][str(face)]['openings'].append(dict(box=box,kind='window',inferred=inferred,source='manual facade rectification' if not inferred else 'occluded row continuation'))
op(0,[.40,.47,.58,.65]);op(0,[.40,.79,.58,.95]);op(0,[.40,.14,.58,.31],True)
for f in [2,3,4]:p['faces'][str(f)]['balconies']=[dict(x0=0,x1=1,floors=[1,2],depth=1.05,rail='stone',evidence='source frontage railings')]
for x in [.25,.72]:
 for y in [.17,.49,.82]:op(5,[x-.09,y-.075,x+.09,y+.075],True)
# Pixel at equipment foot locates the fixture in the plane of its actual roof.
def equip(bid,kind,pix,**kw):
 b=bs[bid];xy=np.array(b['footprint_world']);edge=xy[1]-xy[0];a=np.arctan2(edge[1],edge[0]);R=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]);ctr=xy.mean(0);plan=(xy-ctr)@R;pt=(intersect_z([pix],'frame_044.00.jpg',b['roof_edge_height']-.30)[0,:2]-ctr)@R;pos=(pt-plan.min(0))/(plan.max(0)-plan.min(0));ps[bid]['equipment'].append(dict(type=kind,xy=pos.tolist(),source_image='frame_044.00.jpg',source_foot_px=pix,evidence='source-visible fixture; small dimensions inferred from calibrated image scale',**kw))
for p in ps.values():p['equipment']=[]
equip('P001','tank',[414,671],radius=.47,height=1.2,stand=.6);equip('P001','tank',[476,674],radius=1.12,height=2.20,stand=.03);equip('P001','vent',[470,648],height=1.45)
equip('P002','tank',[565,538],radius=.42,height=1.05,stand=.6);equip('P002','vent',[585,539],height=1.3)
equip('P006','tank',[795,605],radius=.48,height=1.30,stand=.6);equip('P006','vent',[812,598],height=1.3)
equip('P007','vent',[866,541],height=1.2)
equip('P005','vent',[920,814],height=.95);equip('P010','tank',[1054,708],radius=.26,height=.9,stand=.7)
equip('P011','heater',[1253,710],height=.9);equip('P011','roof_ac',[1207,708]);equip('P011','vent',[1275,705],height=1.25)
equip('P012','tank',[602,776],radius=.47,height=1.25,stand=.65);equip('P012','tank',[630,774],radius=.47,height=1.2,stand=.6);equip('P012','vent',[582,784],height=1.2)
(P/'pilot_mesh_input.json').write_text(json.dumps(d,ensure_ascii=False));(P/'pilot_profiles.json').write_text(json.dumps(profiles,indent=2,ensure_ascii=False));print('DETAILED',len(d['entries']),sum(len(p['equipment']) for p in profiles['entries']))
