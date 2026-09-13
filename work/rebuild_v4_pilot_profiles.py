"""Fresh, manually reviewed pilot facade observations. Boxes use rectified images.
Normalized boxes are x-left,y-top,x-right,y-bottom. Hidden rows are labeled inferred.
"""
import json,numpy as np,cv2
from pathlib import Path
P=Path('work/rebuild4/architecture');data=json.loads((P/'pilot_mesh_input.json').read_text());fac=json.loads((P/'facades/manifest.json').read_text())['entries'];F={(x['building_id'],x['face']):x for x in fac};profiles={}
colors={'P001':[.64,.31,.25],'P002':[.68,.70,.68],'P003':[.52,.34,.24],'P003W2':[.52,.34,.24],'P004':[.82,.83,.78],'P005':[.67,.71,.68],'P006':[.75,.78,.75],'P007':[.78,.79,.75],'P008':[.78,.79,.72],'P010':[.62,.64,.57],'P011':[.75,.70,.65],'P012':[.68,.60,.57]}
for b in data['entries']:
 p=dict(id=b['id'],color=colors[b['id']],style='brick' if b['id'].startswith('P003') else 'ceramic',roof_color=(np.array(b['roof_color'])/255).tolist(),roof_age=.18,wall_age=.20,glazing_color=[.12,.16,.14],faces={},equipment=[],roof_patches=[],notes='Source-specific reviewed facade boxes; hidden details carry an inference flag. No source images enter materials.')
 if b['id']=='P001':p['glazing_color']=[.18,.36,.29];p['wall_age']=.08
 if b['id'] in ['P010','P003','P003W2']:p['wall_age']=.55;p['roof_age']=.7
 if b['id']=='P005':p['roof_color']=[.07,.64,.82];p['wall_age']=.65;p['style']='plaster'
 if b['id']=='P004':p['roof_color']=[.17,.27,.33];b['floor_count']=3
 if b['id']=='P012':p['wall_age']=.22
 for j in range(len(b['footprint_world'])):p['faces'][str(j)]=dict(openings=[],balconies=[],equipment=[],color=p['color'],style=p['style'])
 profiles[b['id']]=p

def boxes(b,f,bs,kind='window',inferred=False):
 p=profiles[b]['faces'][str(f)]
 for q in bs:p['openings'].append(dict(box=q,kind=kind,source='manual source rectification' if not inferred else 'inferred repetition in occluded part',inferred=inferred))
def pixels(b,f,bs,**kw):
 d=F[(b,f)];a=np.array([d['rectified_width'],d['rectified_height']]*2);boxes(b,f,[(np.array(q)/a).tolist() for q in bs],**kw)
def repeat(b,f,cols,rows,w,h,inferred=False):
 boxes(b,f,[[x-w/2,y-h/2,x+w/2,y+h/2] for y in rows for x in cols],inferred=inferred)
def balcony(b,f,x0,x1,levels,depth=1.1,rail='stone'):
 profiles[b]['faces'][str(f)]['balconies'].append(dict(x0=x0,x1=x1,floors=levels,depth=depth,rail=rail,evidence='source-visible balcony and parapet; depth estimated from roof recess'))
def ac(b,f,x,y):profiles[b]['faces'][str(f)]['equipment'].append(dict(type='ac',x=x,y=y,evidence='source-visible condenser'))
# Red ceramic house, three storeys. Small vents are not full-size glazed windows.
pixels('P001',0,[[100,35,148,111],[177,35,223,110],[101,181,147,254],[178,182,223,256],[100,330,146,400],[178,330,223,400],[30,329,73,400]])
pixels('P001',0,[[270,11,298,38],[270,365,298,390]],kind='vent')
pixels('P001',2,[[44,32,147,105],[196,31,292,108],[45,173,145,245],[197,171,291,245]])
pixels('P001',2,[[45,320,145,392],[197,320,291,392]],inferred=True)
pixels('P001',3,[[118,38,175,109],[118,177,177,251]])
pixels('P001',3,[[264,57,299,83]],kind='vent');pixels('P001',3,[[351,62,417,157]],kind='door');ac('P001',3,.34,.30);ac('P001',3,.58,.50)
profiles['P001']['roof_color']=[.72,.50,.37]
# Gray four-storey home. Every perimeter segment is preserved, including both recesses.
repeat('P002',0,[.18],[.10,.35,.59,.83],.15,.13);repeat('P002',0,[.49,.75],[.095,.342],.10,.085)
repeat('P002',2,[.56],[.49,.74],.40,.12);repeat('P002',3,[.47,.80],[.10,.34,.59,.83],.21,.135)
repeat('P002',4,[.61],[.12,.39,.64,.86],.51,.15);balcony('P002',4,0,1,[1,2,3],1.05)
boxes('P002',5,[[.25,.03,.94,.20]],kind='door');balcony('P002',5,0,1,[1,2,3],1.10)
repeat('P002',6,[.37,.83],[.115],.17,.125);repeat('P002',6,[.37,.83],[.36,.60,.84],.17,.125,inferred=True)
repeat('P002',7,[.25,.71],[.125,.37,.615,.855],.19,.13);repeat('P002',7,[.405],[.127,.37,.615],.077,.085)
for y in [.47,.72]:
 for x in [.21,.68]:ac('P002',7,x,y)
# Exposed brick and concrete frame, with unglazed holes where observed.
repeat('P003',2,[.76],[.105],.30,.19)
boxes('P003',3,[[.065,.435,.24,.645],[.91,.51,.999,.73],[.055,.81,.17,.99]],kind='empty')
for f in profiles['P003']['faces'].values():f['concrete_frame']=True
for f in profiles['P003W2']['faces'].values():f['concrete_frame']=True
# Blue hip-roof building: quiet back wall plus differently oriented balconies.
repeat('P004',0,[.10],[.14,.455,.78],.075,.15);repeat('P004',0,[.35,.48,.59],[.16,.49],.048,.085);boxes('P004',0,[[.59,.77,.70,.93]])
for x,y in [(.29,.19),(.64,.22),(.52,.54),(.64,.54)]:ac('P004',0,x,y)
for f in [2,4,5,6]:balcony('P004',f,0,1,[1,2],1.15);boxes('P004',f,[[.32,.02,.75,.245]],kind='door')
repeat('P004',7,[.14],[.43],.12,.085)
# Long cyan-roof house: only one small window in the long exposed side.
repeat('P005',0,[.46],[.17],.52,.105);repeat('P005',0,[.32],[.62],.24,.14);repeat('P005',3,[.42],[.28],.060,.10)
# White L plan: balcony railings occupy the recessed street frontage.
repeat('P006',0,[.68],[.255,.575],.14,.14);ac('P006',0,.78,.32);ac('P006',0,.78,.64)
repeat('P006',1,[.40,.81],[.125],.080,.105)
boxes('P006',2,[[.56,.125,.85,.25],[.20,.525,.88,.72]])
balcony('P006',2,0,1,[1,2],1.0);balcony('P006',3,0,1,[1,2],1.0);balcony('P006',4,0,1,[1,2],1.0)
repeat('P006',5,[.67],[.14],.16,.14)
# Neighbor with paired front windows and one narrow side row.
repeat('P007',0,[.27,.78],[.18,.49],.225,.15);repeat('P007',0,[.40,.83],[.87],.115,.14)
repeat('P007',1,[.27],[.18,.515],.145,.16);repeat('P007',1,[.52],[.175,.51],.095,.135);repeat('P007',1,[.91],[.49],.09,.12)
balcony('P007',2,0,1,[1,2],1.05);balcony('P007',3,0,.35,[1,2],1.05)
# Low roof includes a real rectangular opening; the old wall has small masonry vents.
repeat('P010',3,[.15,.28,.43,.59,.73],[.51],.065,.24)
# User's boxed target: asymmetric three-storey cream-pink home, east-side balcony.
pixels('P011',0,[[162,20,215,94],[161,158,213,234]])
pixels('P011',0,[[161,292,213,367]],inferred=True)
pixels('P011',3,[[232,33,278,103],[232,174,278,245],[230,306,278,379]])
pixels('P011',3,[[113,338,145,362]],kind='vent')
repeat('P011',1,[.21,.47],[.315],.125,.15);repeat('P011',1,[.47],[.66],.125,.16);repeat('P011',1,[.21,.47],[.06],.125,.15,inferred=True)
balcony('P011',2,0,1,[1,2],.95,'metal');boxes('P011',2,[[.58,.09,.78,.29]],kind='door')
profiles['P011']['roof_color']=[.73,.57,.46];profiles['P011']['roof_patches']=[dict(rect=[.08,.10,.22,.63],color=[.83,.84,.79]),dict(rect=[.29,.31,.45,.68],color=[.86,.86,.79]),dict(rect=[.54,.08,.65,.34],color=[.80,.81,.74])]
# Pink neighbor has distinct gray side walls and small barred opening rhythm.
profiles['P012']['faces']['1']['color']=[.68,.74,.73]
repeat('P012',1,[.17,.70],[.17,.49,.82],.16,.14);repeat('P012',1,[.43],[.17,.49,.82],.07,.14)
repeat('P012',2,[.295,.78],[.16,.48],.19,.14);repeat('P012',0,[.81],[.19],.15,.14)
boxes('P012',3,[[.105,.065,.28,.25],[.40,.11,.48,.205],[.61,.105,.77,.20]]);boxes('P012',3,[[.12,.39,.26,.60]],inferred=True)
# Every roof object here is annotated separately later; no arbitrary auto tank population.
(P/'pilot_profiles.json').write_text(json.dumps(dict(entries=list(profiles.values()),status='manually reviewed primary facade layouts; unseen pieces explicitly inferred'),indent=2));(P/'pilot_mesh_input.json').write_text(json.dumps(data,ensure_ascii=False));print('PROFILES',len(profiles),'OPENINGS',sum(len(f['openings']) for p in profiles.values() for f in p['faces'].values()))
