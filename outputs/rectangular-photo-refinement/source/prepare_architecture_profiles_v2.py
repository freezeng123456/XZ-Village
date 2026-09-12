"""Source-aware facade profiles: rectangular building grammar plus documented visual overrides."""
from pathlib import Path
import json,numpy as np,hashlib
root=Path.cwd();base=root/'work/buildings/v2';bs=json.loads((base/'inventory.json').read_text())['buildings'];finishes=json.loads((root/'work/buildings/surface_finishes.json').read_text());result={}
def srgb(linear):
 a=np.array(linear);return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055).tolist()
for b in bs:
 bid=b['id'];W=b['rectangle']['width'];D=b['rectangle']['depth'];H=b['roof_height']-b['base_height'];n=b['floors'];f=finishes[bid];wall=np.array(srgb(np.array(f['wall'])/1.4));roof=np.array(b.get('roof_texture',{}).get('rgb',srgb(np.array(f['roof'])/1.4) if f.get('roof') else [.68,.67,.61]));style='ceramic';age=.10
 if b['type']=='gable':style='aged_plaster';wall=np.array([.49,.47,.41]);age=.34
 elif b.get('finish_style')=='weathered_concrete':style='aged_plaster';age=.4;wall=np.clip(wall,.34,.72)
 elif b.get('finish_style')=='exposed_brick':style='brick';wall=np.array([.56,.32,.22]);age=.22
 elif n==1:style='paint';age=.20
 if b.get('public_hall'):wall=np.array([.62,.20,.13]);style='paint';age=.14
 facades=[]
 for j,L in enumerate([W,D,W,D]):
  face_sources=[x for x in b.get('visible_facades',[]) if x.get('v2_edge',x['edge'])==j];source=max(face_sources,key=lambda x:x['source_visible_pixels'],default=None);color=wall.copy()
  if source and b['type']!='gable' and style!='brick':
   found=f['faces'].get(str(source['edge']),{});c=found.get('rgb')
   if c and found['pixels']>1000:
    observed=np.array(srgb(np.array(c)/1.4))
    if np.linalg.norm(observed-wall)<.24:color=wall*.65+observed*.35
  count=max(1,min(5,int(L/3.0)));centers=list(np.linspace(1/(count+1),1-1/(count+1),count));layout_evidence='Estimated regular storey and column layout'
  if source and source['source_visible_pixels']>1000:
   L0=source.get('v1_edge_length',L);candidates=[a for a in source['opening_candidates'] if a[1]-a[0]>.65 and a[3]-a[2]>.85 and a[2]>H*.30];xvals=sorted([(a[0]+a[1])/2/L0 for a in candidates if .07<(a[0]+a[1])/2/L0<.93]);groups=[]
   for x in xvals:
    k=next((k for k,g in enumerate(groups) if abs(np.mean(g)-x)<.10),None)
    if k is None:groups.append([x])
    else:groups[k].append(x)
   if 1<=len(groups)<=5:centers=[float(np.mean(g)) for g in groups];layout_evidence='Source opening columns regularized into consistent storeys; missing rows inferred'
  windows=[]
  for floor in range(n):
   for cx in centers:windows.append(dict(x=cx,z=(floor+.62)/n,width=min(.88 if b['type']=='gable' else 1.25,L*.24),height=min(.95 if b['type']=='gable' else 1.65,H/n*.57),kind='window'))
  facades.append(dict(edge=j,color=color.tolist(),style=style,age=age,windows=windows,loggias=[],layout_evidence=layout_evidence,source_pixels=source['source_visible_pixels'] if source else 0))
 result[bid]=dict(id=bid,wall_color=wall.tolist(),style=style,age=age,roof_color=np.clip(roof,.20,.88).tolist(),facades=facades,roof_zones=[],tanks=[],roof_partition=None,cornice='double',baluster='metal',manual_source_review=False)
# The following profiles come from direct inspection of 4K source crops, not dark-pixel detections.
def override(bid,color,style,age):
 p=result[bid];p.update(wall_color=color,style=style,age=age,manual_source_review=True)
 for f in p['facades']:f.update(color=color,style=style,age=age,layout_evidence='4K source crop visually reviewed; unseen lower rows inferred')
 return p
# Window tuples use fractional facade x/z and physical opening width/height.
def windows(p,edge,rows):p['facades'][edge]['windows']=[dict(x=x,z=z,width=w,height=h,kind=k if len(row)==5 else 'window') for row in rows for x,z,w,h,*rest in [row] for k in [rest[0] if rest else 'window']]
def repeated(xs,floors=3,width=1.45,height=1.75):return [(x,(f+.62)/floors,width,height) for f in range(floors) for x in xs]
p=override('B005',[.67,.61,.57],'paint',.13);p['roof_color']=[.83,.82,.76];p['roof_zones']=[dict(y0=.51,y1=1,color=[.73,.65,.50])];p['roof_partition']=.51;p['tanks']=[dict(x=.48,y=.56,height=2.55,radius=.38),dict(x=.36,y=.57,height=1.90,radius=.27)]
windows(p,0,[(.18,.79,1.5,.6),(.39,.78,.9,.48),(.69,.74,2.45,2.0),(.69,.43,1.45,1.15),(.19,.42,1.35,1.55),(.20,.13,1.35,1.55),(.69,.13,1.35,1.55)]);windows(p,1,repeated([.42],width=2.0,height=1.85));p['facades'][0]['accent_recesses']=[dict(x=.69,z=.74,width=2.75,height=2.3,depth=.42)]
p=override('B006',[.66,.285,.22],'paint',.12);p['roof_color']=[.68,.49,.43];p['tanks']=[dict(x=.19,y=.72,height=2.15,radius=.34)];p['roof_utility_box']=dict(x=.55,y=.57);windows(p,0,repeated([.10,.57],width=1.4,height=1.75)+[(.30,.80,.88,.6),(.30,.48,.8,.55)]);windows(p,1,repeated([.30,.58],width=1.60,height=1.75));p['ac_windows']=[dict(edge=0,x=.57,z=.66),dict(edge=0,x=.33,z=.37)]
p=override('B008',[.76,.77,.73],'ceramic_horizontal',.12);p['roof_color']=[.86,.86,.81];p['tanks']=[dict(x=.13,y=.78,height=2.35,radius=.35)];p['baluster']='stone';p['facades'][0]['loggias']=[dict(x0=.33,x1=.99,floors=[1,2],depth=1.05,columns=3)];p['facades'][1]['loggias']=[dict(x0=.0,x1=.22,floors=[1,2],depth=.88,columns=2)];windows(p,0,repeated([.15],width=1.35,height=1.70));windows(p,1,repeated([.64],width=1.65,height=1.80));p['cornice']='layered'
p=override('B010',[.78,.79,.73],'aged_plaster',.70);p['roof_color']=[.86,.87,.83];p['facades'][0]['loggias']=[dict(x0=.58,x1=.99,floors=[2],depth=1.05,columns=2)];p['facades'][1]['loggias']=[dict(x0=.0,x1=.62,floors=[2],depth=.95,columns=2)];p['baluster']='stone';windows(p,0,repeated([.20,.46,.75],width=1.65,height=1.80));windows(p,1,repeated([.45,.80],width=1.45,height=1.7));p['cornice']='layered';p['facades'][0]['stains']=[dict(x=.17,z=.28,rx=.18,rz=.14,strength=.68),dict(x=.42,z=.38,rx=.20,rz=.10,strength=.63),dict(x=.13,z=.05,rx=.20,rz=.12,strength=.70)]
p=override('B012',[.73,.75,.70],'aged_plaster',.25);p['roof_color']=[.86,.87,.82];p['tanks']=[dict(x=.22,y=.76,height=2.25,radius=.36)];p['facades'][0]['loggias']=[dict(x0=.67,x1=.99,floors=[1,2],depth=.9,columns=2)];p['facades'][1]['loggias']=[dict(x0=.02,x1=.70,floors=[1,2],depth=1.0,columns=3)];windows(p,0,repeated([.15,.47],width=1.45,height=1.65));p['cornice']='dark_band'
p=override('B014',[.79,.77,.70],'ceramic',.08);p['roof_color']=[.21,.32,.39];p['facades'][1]['loggias']=[dict(x0=.05,x1=.91,floors=[1,2],depth=1.05,columns=3)];p['baluster']='stone';windows(p,0,[(.13,.79,1.15,1.85),(.13,.47,1.1,1.7),(.70,.24,.66,.7)]);p['cornice']='layered'
# Older concrete and brick fronts are visibly different from pale tiled houses.
for bid in ['B004','B032','B033','C001','C002','C003','C004','C005']:
 result[bid]['manual_source_review']=True
 if bid.startswith('B03') or bid=='C002':result[bid]['age']=.28
# Additional near-field profiles inspected against source_contact_1..4.jpg.
near={
 'B002':([.72,.73,.68],'aged_plaster',.38), 'B003':([.72,.72,.66],'ceramic_horizontal',.16),
 'B004':([.63,.64,.59],'aged_plaster',.75), 'B007':([.70,.71,.68],'ceramic',.18),
 'B009':([.72,.80,.66],'paint',.12), 'B011':([.73,.75,.70],'ceramic_horizontal',.15),
 'B013':([.70,.71,.68],'ceramic',.19), 'B015':([.66,.67,.60],'aged_plaster',.55),
 'B016':([.74,.76,.67],'paint',.24), 'B017':([.77,.82,.74],'paint',.12),
 'B018':([.65,.73,.70],'ceramic',.13), 'B019':([.76,.79,.71],'aged_plaster',.37),
 'B020':([.76,.78,.70],'aged_plaster',.29), 'B021':([.80,.78,.59],'paint',.18),
 'B022':([.72,.73,.65],'ceramic',.18), 'B023':([.75,.80,.73],'paint',.18),
 'B024':([.72,.76,.71],'aged_plaster',.38), 'B025':([.79,.76,.64],'paint',.15),
 'B026':([.73,.61,.54],'paint',.13), 'B027':([.80,.78,.66],'paint',.12),
 'B028':([.73,.73,.65],'aged_plaster',.33), 'B029':([.74,.73,.69],'ceramic',.14),
 'B030':([.69,.62,.51],'ceramic',.17), 'B031':([.75,.77,.70],'aged_plaster',.28),
 'B032':([.60,.35,.24],'brick',.28), 'B033':([.60,.35,.24],'brick',.30),
 'B034':([.74,.75,.69],'ceramic',.20), 'B035':([.68,.75,.68],'ceramic_horizontal',.21),
 'C001':([.64,.67,.61],'aged_plaster',.80), 'C002':([.60,.35,.24],'brick',.23),
 'C003':([.74,.74,.66],'ceramic',.26), 'C004':([.75,.77,.70],'ceramic',.17),
 'C005':([.70,.71,.66],'aged_plaster',.45)}
for bid,(color,style,age) in near.items():override(bid,color,style,age)
result['B002']['roof_color']=[.13,.66,.76];windows(result['B002'],0,[(.58,.65,.70,1.35),(.58,.18,.70,1.25)])
result['B006']['glazing_color']=[.22,.39,.28];result['B006']['ac_windows']=[dict(edge=0,x=.57,z=.72),dict(edge=0,x=.33,z=.315)]
# Rectangular recessed verandas preserve a stable core while matching the photographed corner treatment.
for bid,x0,floors,side in [('B003',.62,[1,2],.55),('B007',.63,[2],.25),('B009',.68,[2],.26),('B011',.44,[2],.35),('B013',.57,[1,2],.22),('B017',.59,[1,2],.30),('B018',.65,[2],.28),('B019',.58,[1,2],.45),('B020',.53,[2],.40),('B021',.53,[1,2],.32),('B022',.15,[1,2],.73),('B024',.40,[2],.35),('B028',.43,[2],.65),('B030',.60,[2],.38),('B031',.55,[2],.38),('B034',.40,[2],.60),('C003',.56,[1],.47),('C004',.14,[1,2],.72)]:
 p=result[bid];p['facades'][0]['loggias']=[dict(x0=x0,x1=.985,floors=floors,depth=1.05,columns=2 if x0>.5 else 3,arched=bid not in ['B007','B009','B013','B017','B021'])];p['facades'][1]['loggias']=[dict(x0=.01,x1=side,floors=floors,depth=.90,columns=2)];p['baluster']='stone';p['cornice']='layered'
for bid in ['B008','B010','B012','B014']:
 for f in result[bid]['facades']:
  for log in f['loggias']:log['arched']=bid in ['B008','B010']
for bid in ['B009','B017','B019','B020','B022','B024','B028','B030','C004']:
 result[bid]['accent_color']=[.47,.29,.27]
for bid in ['B004','B015','B016','B032','B033','C001']:
 result[bid]['roof_color']=[.49,.48,.41];result[bid]['roof_age']=.76
for bid in ['B032','B033']:result[bid]['concrete_frame']=True
for bid in ['B019','B024','B028','B031','C001']:
 result[bid]['facades'][0]['stains']=[dict(x=.25,z=.27,rx=.15,rz=.23,strength=.46),dict(x=.62,z=.12,rx=.25,rz=.16,strength=.50)]
result['C001']['facades'][0]['stains'].append(dict(x=.5,z=.58,rx=.17,rz=.40,strength=.8))
result['B029']['roof_zones']=[dict(y0=.10,y1=.25,color=[.88,.87,.82]),dict(y0=.45,y1=.55,color=[.86,.85,.80])]

# Further source-camera review: roof topology, terrace fixtures and visible verandas.
for b in bs:
 if b.get('source_roof_review'):
  p=result[b['id']];p['manual_source_review']=True
  if b['type']=='flat':
   p['style']='aged_plaster';p['age']=.42
   for f in p['facades']:f.update(style='aged_plaster',age=.42)
for bid in ['O061','O063']:override(bid,[.74,.65,.40],'aged_plaster',.3)
override('O064',[.72,.39,.21],'paint',.18)
for bid in 'O003 O008 O020 O045 O054 O055 O056 O065 O090 O091'.split():result[bid]['roof_color']=[.57,.36,.25]
for bid in 'O024 O041 O044 O057 O058 O059 O094 O095'.split():result[bid]['roof_color']=[.43,.44,.39]
result['D001']['roof_surface']='metal';result['D001']['roof_color']=[.8,.22,.18];result['D001']['manual_source_review']=True
result['O003']['roof_pavers']='hex'
for bid in 'R001 R002 R004 R007 R011 R013 R021 R022 R023 R027'.split():
 result[bid]['tanks']=[dict(x=.72,y=.75,height=2.05,radius=.33)];result[bid]['manual_source_review']=True
result['R004']['tanks'].append(dict(x=.24,y=.23,height=1.75,radius=.28))
for bid in ['R028','R029']:result[bid]['solar_water_heater']=True;result[bid]['manual_source_review']=True
for bid in 'A002 A003 A005 A008 A010 A014 A018 A019 A020 A021 A023 A024 A028 A031 A032 A033 A034 A036 A037 A038 A040 A041 A047 A049 A050 N002 N003 N005 N015 N017 F004 F005 F006 F007 F008 F009 F010 F012'.split():
 p=result[bid];b=next(b for b in bs if b['id']==bid);n=b['floors'];floors=list(range(max(1,n-2),n));x0=.12 if bid in ['A014','A033','A034','A041','A050','N003','N017','F004'] else (.02 if bid in ['A038','N015'] else .58);x1=.55 if bid in ['A038','N015'] else .985
 p['facades'][0]['loggias']=[dict(x0=x0,x1=x1,floors=floors,depth=.95,columns=3 if x0<.2 else 2,arched=bid in ['A047','F004','N005'])];p['baluster']='stone';p['cornice']='layered';p['manual_source_review']=True
 if bid in ['A002','A008','A018','A019','A028','A036','A037','A040','N002']:p['facades'][1]['loggias']=[dict(x0=.01,x1=.3,floors=floors,depth=.85,columns=2)]
for bid in ['B004','C001']:result[bid]['roof_utility_box']=dict(x=.54,y=.57)
for bid in ['B029','R013','A016','A018','A023']:result[bid]['roof_patchwork']=True
# Source-localized rooftop cylinders are reused as inferred, full-height water tanks on frames.
fixtures=json.loads((root/'work/buildings/observed_roof_fixtures.json').read_text())
for b in bs:
 p=result[b['id']]
 if p['tanks']:continue
 q=np.array(b['roof_world']);u=(q[1]-q[0]);u/=np.linalg.norm(u);v=(q[3]-q[0]);v/=np.linalg.norm(v)
 for item in fixtures:
  if item['building_id']!=b['id'] or item['kind']!='tank':continue
  d=np.array(item['world_center'])-q[0];p['tanks'].append(dict(x=float(np.clip(d@u/b['rectangle']['width'],.12,.88)),y=float(np.clip(d@v/b['rectangle']['depth'],.12,.88)),height=2.2,radius=.34))
(base/'profiles.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('SOURCE_PROFILES',len(result),'manual',(sum(p['manual_source_review'] for p in result.values())))
