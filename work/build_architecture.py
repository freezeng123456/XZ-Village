"""Editable, individually inventoried architectural reconstruction candidates.

Source-supported roof traces are distinct from estimated occluded facades.
This script does not mark a building accepted merely because it generated.
"""
import bpy,json,math,random,os
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.geometry import tessellate_polygon
ROOT=Path.cwd();OUT=ROOT/os.environ.get('ARCHITECTURE_OUT','outputs/building-quality');OUT.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene;s.view_layers[0].material_override=None
for c in list(bpy.data.collections):
 if c.name.startswith(('04 ','06 ','09 ','10 ')):c.hide_render=True;c.hide_viewport=True
incremental=set(filter(None,os.environ.get('BUILD_IDS','').split(',')))
parent=next((c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE')),None)
if parent is None:parent=bpy.data.collections.new('11 ARCHITECTURE | numbered editable candidates');s.collection.children.link(parent)
if incremental:
 for c in list(parent.children):
  if c.name.split(' | ')[0] in incremental:
   for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
   bpy.data.collections.remove(c)
def mat(name,rgb,rough=.8,noise=False,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if noise:
  n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=9;n.inputs['Detail'].default_value=4;b=m.node_tree.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.18;b.inputs['Distance'].default_value=.022;m.node_tree.links.new(n.outputs['Fac'],b.inputs['Height']);m.node_tree.links.new(b.outputs[0],p.inputs['Normal'])
  ramp=m.node_tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(v*.76 for v in rgb),1);ramp.color_ramp.elements[1].color=(*(min(1,v*1.08) for v in rgb),1);m.node_tree.links.new(n.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color'])
 return m
trim=mat('Architecture / ivory stone coping',(.7,.69,.64),noise=True);dark=mat('Architecture / deep reveals',(.022,.025,.023));glass=mat('Architecture / green-grey glass',(.085,.17,.15),.25,metal=.35);metal=mat('Architecture / dark window aluminium',(.04,.045,.043),.35,metal=.65);steel=mat('Architecture / tank stainless steel',(.51,.54,.54),.32,metal=.8);roofmat=mat('Architecture / weathered cement roof',(.41,.42,.38),noise=True);blue=mat('Architecture / blue sheet roofing',(.025,.36,.53),.48,metal=.25);blueTile=mat('Architecture / slate blue glazed roof tiles',(.09,.16,.23),.45);joint=mat('Architecture / mortar joints',(.24,.25,.23));terracotta=mat('Architecture / terracotta terrace tiles',(.49,.26,.18),noise=True)
wood=mat('Architecture / aged timber',(.15,.105,.063),noise=True);stone=mat('Architecture / old masonry',(.39,.36,.29),noise=True)
def mesh(name,verts,faces,material):
 verts=[(v[0],v[1],v[2]+BASE) for v in verts];me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(BID+' / '+name,me);C.objects.link(o);me.materials.append(material);o['building_id']=BID;return o
def box(name,loc,dim,material,angle=0,bevel=0):
 a,b,c=[v/2 for v in dim];o=mesh(name,[(i*a,j*b,k*c) for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]],[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)],material);o.location=loc;o.rotation_euler.z=angle
 if bevel:m=o.modifiers.new('Small edge radius','BEVEL');m.width=bevel;m.segments=2
 return o
def line(name,pts,r,material):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for a,p in zip(sp.points,pts):a.co=(p[0],p[1],p[2]+BASE,1)
 o=bpy.data.objects.new(BID+' / '+name,cu);C.objects.link(o);cu.materials.append(material);o['building_id']=BID;return o
def cylinder(name,loc,r,h,material):
 n=20;v=[(loc[0]+r*math.cos(i*2*math.pi/n),loc[1]+r*math.sin(i*2*math.pi/n),loc[2]+z) for z in [-h/2,h/2] for i in range(n)];return mesh(name,v,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],material)
def slab(name,poly,z,thick,material):
 p=np.array(poly);p[:,2]=z;v=[Vector(q) for q in p];faces=[]
 for tri in tessellate_polygon([v]):faces.append(tuple(int(q) if isinstance(q,int) else min(range(len(v)),key=lambda i:(v[i]-q).length) for q in tri))
 n=len(p);vv=np.vstack([p,p+[0,0,thick]]);ff=[tuple(reversed(f)) for f in faces]+[tuple(i+n for i in f) for f in faces]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];return mesh(name,vv,ff,material)
poses=json.loads((ROOT/'work/buildings/visibility/poses.json').read_text()) if (ROOT/'work/buildings/visibility/poses.json').exists() else {}
imagecache={}
def source_material(name,fallback,info):
 pose=poses[str(info['source_time'])];m=fallback.copy();m.name=name;n=m.node_tree.nodes;bsdf=n.get('Principled BSDF');source=ROOT/pose['source']
 if str(source) not in imagecache:imagecache[str(source)]=bpy.data.images.load(str(source),check_existing=True)
 tex=n.new('ShaderNodeTexImage');tex.image=imagecache[str(source)];tex.extension='CLIP';mask=n.new('ShaderNodeTexImage');mask.image=bpy.data.images.load(str(ROOT/info['mask']),check_existing=True);mask.image.colorspace_settings.name='Non-Color';mask.extension='CLIP';mix=n.new('ShaderNodeMixRGB')
 if 'mask_bounds_px' in info:
  x,y,w,h=info['mask_bounds_px'];uv=n.new('ShaderNodeTexCoord');sub=n.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=(x/1600,1-(y+h)/900,0);mul=n.new('ShaderNodeVectorMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=(1600/w,900/h,1);m.node_tree.links.new(uv.outputs['UV'],sub.inputs[0]);m.node_tree.links.new(sub.outputs[0],mul.inputs[0]);m.node_tree.links.new(mul.outputs[0],mask.inputs['Vector'])
 if bsdf.inputs['Base Color'].is_linked:old=bsdf.inputs['Base Color'].links[0].from_socket;m.node_tree.links.new(old,mix.inputs[1])
 else:mix.inputs[1].default_value=bsdf.inputs['Base Color'].default_value
 m.node_tree.links.new(mask.outputs['Color'],mix.inputs[0]);m.node_tree.links.new(tex.outputs['Color'],mix.inputs[2]);m.node_tree.links.new(mix.outputs[0],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.8
 return m,pose
def project_uv(o,pose):
 if o.type!='MESH':return
 rot=np.array([[math.cos(o.rotation_euler.z),-math.sin(o.rotation_euler.z),0],[math.sin(o.rotation_euler.z),math.cos(o.rotation_euler.z),0],[0,0,1]]);local=np.array([v.co[:] for v in o.data.vertices]);world=local@rot.T+np.array(o.location);pc=world@np.array(pose['rotation']).T+np.array(pose['translation']);xy=pc[:,:2]/pc[:,2,None];rad=1+pose['radial']*(xy*xy).sum(1);px=xy*rad[:,None]*pose['focal']+[800,450];uv=o.data.uv_layers.new(name='Visibility-filtered source UV')
 for loop in o.data.loops:uv.data[loop.index].uv=(px[loop.vertex_index,0]/1600,1-px[loop.vertex_index,1]/900)
# Sparse, manually reviewed visible-front placement. Unseen lower floors remain estimates.
# Values are horizontal centres relative to the traced front edge; upper rows only
# when the image is occluded. Each opening remains an editable recess and frame.
front={
 'B002':([.61],[.79],.65,1.05),'B003':([.18,.67],[.81],1.25,1.7),
 'B004':([.23,.7],[.6],1.1,1.4),'B005':([.16,.4,.74],[.84],1.35,1.7),
 'B006':([.15,.36,.62],[.84,.56],1.15,1.7),'B007':([.12,.43,.76],[.88],1.25,1.7),
 'B008':([.18,.55,.84],[.84,.56],1.5,1.8),'B009':([.18,.5,.83],[.84,.57],1.35,1.35),
 'B010':([.16,.5,.82],[.84,.56,.3],1.25,1.7),'B011':([.3,.72],[.84],1.3,1.6),
 'B012':([.18,.62],[.85],1.3,1.7),'B013':([.22,.71],[.86,.57],1.35,1.75),
 'B014':([.62],[.46],.6,.65),'B015':([.3,.62],[.77],1.45,1.7),
 'B016':([.3,.6,.82],[.85],1.15,1.5),'B017':([.22,.64],[.83],1.3,1.65),
 'B018':([.25],[.82,.55],1.35,1.7),'B019':([.22,.5],[.84,.56,.3],1.35,1.7),
 'B020':([.2,.51],[.82,.53],1.25,1.7),'B021':([.24,.69],[.83,.54],1.3,1.65),
 'B022':([.25,.68],[.82,.54],1.35,1.7),'B023':([.3,.72],[.83],1.5,1.8),
 'B024':([.24,.61],[.85,.56,.3],1.1,1.55),'B025':([.18,.49,.8],[.83,.56],1.1,1.55),
 'B026':([.22,.52,.81],[.83,.56],1.2,1.7),'B027':([],[],1,1),
 'B028':([.2,.6],[.82,.55],1.3,1.75),'B029':([.2,.6],[.83],1.25,1.7),
 'B030':([.2,.6],[.81,.54],1.3,1.7),'B031':([.25],[.82,.55],1.3,1.7)}
colors={'B002':(.48,.49,.45),'B003':(.55,.55,.5),'B004':(.37,.37,.32),'B005':(.52,.43,.4),'B006':(.49,.18,.135),'B007':(.51,.5,.46),'B008':(.65,.67,.64),'B009':(.54,.64,.51),'B010':(.62,.65,.62),'B014':(.72,.72,.66),'B021':(.65,.6,.42),'B024':(.51,.55,.49),'B025':(.69,.61,.4),'B026':(.61,.58,.46),'B027':(.66,.62,.4)}
balconies={'B005':[.68],'B008':[.65,.35],'B009':[],'B012':[.65],'B013':[.65,.35],'B014':[.65,.35],'B015':[.95],'B019':[.65,.35],'B020':[.65],'B021':[.65,.35],'B022':[.65,.35],'B023':[.65,.35],'B028':[.65,.35],'B030':[.65],'B031':[.65]}
tanks={'B002':(.48,.48),'B005':(.35,.55),'B006':(.53,.55),'B008':(.55,.48),'B012':(.65,.48),'B028':(.5,.5),'B029':(.27,.4),'B030':(.45,.5),'B031':(.6,.55)}
fixtures=json.loads((ROOT/'work/buildings/observed_roof_fixtures.json').read_text()) if (ROOT/'work/buildings/observed_roof_fixtures.json').exists() else []
vispath=ROOT/'work/buildings/visibility/architecture_visibility.json';data=json.loads((vispath if vispath.exists() else ROOT/'work/buildings/architecture_candidates.json').read_text());ledger=[]
if incremental:
 ledger=[b for b in (json.loads((OUT/'building_ledger.json').read_text()) if (OUT/'building_ledger.json').exists() else []) if b['id'] not in incremental]
 data['buildings']=[b for b in data['buildings'] if b['id'] in incremental]
for b in data['buildings']:
 BID=b['id'];C=bpy.data.collections.new(BID+' | '+b['name']);parent.children.link(C);C['status']='Editable candidate; visual acceptance pending';C['source_frame_seconds']=b['t'];C['roof_support_points']=b['roof_support'];C['unobserved_geometry']='Ground level, wall thickness, hidden openings and detail dimensions estimated; no survey.'
 BASE=b.get('base_height',0);p=np.array(b['roof_world']);p[:,2]-=BASE;h=b['roof_height']-BASE;cent=p.mean(0);wall=mat(BID+' / source-matched wall tone',colors.get(BID,(.64,.65,.59)),noise=True)
 C['estimated_ground_height']=BASE;C['roof_height']=b['roof_height'];C['ground_evidence']=b.get('base_height_evidence','Estimated')
 if b.get('finish_style')=='exposed_brick':
  wall=mat(BID+' / exposed clay brick',(.4,.235,.15),noise=True);n=wall.node_tree.nodes;brick=n.new('ShaderNodeTexBrick');brick.inputs['Scale'].default_value=4;brick.inputs['Mortar Size'].default_value=.02;brick.inputs['Color1'].default_value=(.38,.17,.09,1);brick.inputs['Color2'].default_value=(.54,.28,.16,1);brick.inputs['Mortar'].default_value=(.3,.3,.26,1);geom=n.new('ShaderNodeNewGeometry');wall.node_tree.links.new(geom.outputs['Position'],brick.inputs['Vector']);wall.node_tree.links.new(brick.outputs['Color'],n.get('Principled BSDF').inputs['Base Color'])
 if b['type']=='gable':
  wall=mat(BID+' / estimated aged plaster',(.45,.41,.32),noise=True)
  front[BID]=([.22,.76],[.69],.65,.7)
  if b.get('public_hall'):wall=mat(BID+' / red public hall plaster',(.46,.065,.04),noise=True)
 elif BID not in front:
  L0=np.linalg.norm(p[1]-p[0]);xs=[.3,.72] if L0>5 else [.5];front[BID]=(xs,[.82-i*.3 for i in range(b['floors'])],1.2,1.6)
  C['opening_layout']='Estimated consistent storey pattern; individual source placement not accepted.'
 slab('Ground floor closed slab',p,0,.18,roofmat)
 for fz in np.linspace(0,h,b['floors']+1)[1:]:
  if b['type']!='construction':slab('Structural floor slab',p,fz-.18,.18,roofmat)
 opening_count=0
 for j,(v,w) in enumerate(zip(p,np.roll(p,-1,axis=0))):
  u=(w-v);L=np.linalg.norm(u[:2]);u/=L;n=np.array([u[1],-u[0],0]);angle=math.atan2(u[1],u[0]);v=v.copy();v[2]=0
  def at(x,z,depth=0):return v+u*x+n*depth+np.array([0,0,z])
  holes=[]
  if j==0:
   xs,zs,ww,hh=front[BID]
   for xx in xs:
    for zz in zs:
     cx=L*xx;cz=h*zz;a0=max(.12,cx-ww/2);a1=min(L-.12,cx+ww/2);z0=max(.35,cz-hh/2);z1=min(h-.35,cz+hh/2)
     if a1-a0>.3 and z1-z0>.3:holes.append([a0,a1,z0,z1])
  observed=next((f for f in b.get('visible_facades',[]) if f['edge']==j),None);facemat=wall;facepose=None
  if observed:
   holes=observed['opening_candidates'];facemat,facepose=source_material(BID+f' / edge {j} visible source',wall,observed)
  else:
   holes=[]
  # Traced opening coordinates must fit corrected footprints before subdivision.
  holes=[[max(.12,a),min(L-.12,z),max(.12,c),min(h-.2,d)] for a,z,c,d in holes]
  holes=[q for q in holes if q[1]-q[0]>.3 and q[3]-q[2]>.3]
  # The user explicitly authorizes plausible completion of unseen details.
  # Keep measured candidates and fill only otherwise empty facades.
  if not holes and L>2.5:
   ww=min(.8 if b['type']=='gable' else 1.25,L*.23);hh=min(.85 if b['type']=='gable' else 1.55,h*.4)
   count=max(1,min(5,int(L/3.2)))
   for cx in np.linspace(L/(count+1),L-L/(count+1),count):
    for floor in range(b['floors']):
     cz=(floor+.62)*h/b['floors']
     if cz+hh/2<h-.2:holes.append([cx-ww/2,cx+ww/2,cz-hh/2,cz+hh/2])
  if b.get('public_hall') and j==0:holes=[[L*.16,L*.84,.18,h*.86]]
  if j==0 and b['type']!='gable' and L>2.4:
   dw=min(1.2,L*.2);cx=L*.5;door=[cx-dw/2,cx+dw/2,.12,min(2.3,h-.3)]
   holes=[q for q in holes if q[1]<door[0]-.12 or q[0]>door[1]+.12 or q[2]>door[3]+.12];holes.append(door)
   if b['type']!='construction':
    box('Estimated entrance door',at(cx,(door[2]+door[3])/2,-.16),(dw,.06,door[3]-door[2]),wood if b.get('finish_style') else metal,angle)
    box('Entrance step',at(cx,.09,.25),(dw+.3,.62,.18),stone,angle)
    line('Door pull handle',[at(cx+dw*.3,.94,.05),at(cx+dw*.3,1.26,.05)],.014,steel)
  cutsx=sorted(set([0,L]+[q for a in holes for q in a[:2]]));cutsz=sorted(set([0,h]+[q for a in holes for q in a[2:]]))
  for x0,x1 in zip(cutsx[:-1],cutsx[1:]):
   for z0,z1 in zip(cutsz[:-1],cutsz[1:]):
    if any(a<(x0+x1)/2<b0 and c<(z0+z1)/2<d for a,b0,c,d in holes):continue
    o=box('Wall panel with true opening',at((x0+x1)/2,(z0+z1)/2,-.1),(x1-x0,.2,z1-z0),facemat,angle)
    if facepose:project_uv(o,facepose)
  for x0,x1,z0,z1 in holes:
   opening_count+=1;cx=(x0+x1)/2;cz=(z0+z1)/2;ww=x1-x0;hh=z1-z0
   if b['type']=='construction':continue
   if z0<.2:
    for xx in [x0,x1]:box('Entrance vertical jamb',at(xx,cz,.025),(.09,.2,hh),trim,angle)
    box('Entrance head',at(cx,z1,.025),(ww+.12,.2,.09),trim,angle)
    continue
   box('Recessed interior shadow',at(cx,cz,-.21),(ww,.025,hh),dark,angle)
   o=box('Recessed glazing',at(cx,cz,-.1),(ww-.08,.025,hh-.08),glass,angle)
   if facepose:project_uv(o,facepose)
   for xx in [x0,cx,x1]:box('Window vertical aluminium frame',at(xx,cz,.022),(.037,.08,hh),metal,angle,.004)
   for zz in [z0,z1]:box('Window horizontal frame',at(cx,zz,.022),(ww,.08,.04),metal,angle,.004)
   box('Stone window sill',at(cx,z0-.035,.075),(ww+.14,.28,.08),trim,angle,.008)
   for xx in np.arange(x0+.12,x1-.05,.18):line('Security bar',[at(xx,z0+.03,.08),at(xx,z1-.03,.08)],.009,metal)
   line('Security crossbar',[at(x0,cz,.08),at(x1,cz,.08)],.012,metal)
  # Three-level roof edge and independently editable parapet coping.
  edge_finish=roofmat if b.get('finish_style') else trim
  for dz,dep,th in ([(0,.28,.14),(.14,.37,.09)] if b['type']!='gable' and not b.get('finish_style') else [(0,.25,.15)]):box('Projecting roof cornice' if b['type']!='gable' else 'Timber eaves fascia',at(L/2,h+dz,.03),(L+.16,dep,th),edge_finish if b['type']!='gable' else wood,angle,.012)
  if b['type'] in ('flat','solar'):
   box('Low roof parapet',at(L/2,h+.43,-.02),(L,.18,.48),wall,angle,.012);box('Parapet cap',at(L/2,h+.7,-.02),(L+.06,.27,.075),trim,angle,.008)
  if b['type']!='gable':
   for fz in np.linspace(0,h,b['floors']+1)[1:-1]:box('Storey string course',at(L/2,fz,.045),(L,.065,.075),edge_finish,angle)
   box('Ground plinth',at(L/2,.18,.02),(L,.09,.25),stone,angle)
  if j==0 and b['type'] not in ('gable','construction') and L>4:
   q=at(L*.16,min(2.65,h-.5),.23);box('Estimated exterior air conditioner',q,(.78,.4,.55),trim,angle,.025)
   for off in np.linspace(-.22,.22,8):line('Condenser grille',[q+u*off+n*.21+[0,0,-.19],q+u*off+n*.21+[0,0,.19]],.009,metal)
   line('Condenser drain hose',[q+[0,0,-.27],q+[0,0,-.65]],.012,trim)
  if j==0:
   if b['type']=='gable' and not b.get('public_hall'):
    dc=L*.49;dw=min(1.3,L*.22);box('Estimated timber entrance door',at(dc,1.1,.025),(dw,.07,2.2),wood,angle)
    for xx in np.linspace(dc-dw/2,dc+dw/2,7):line('Timber door plank seam',[at(xx,.08,.07),at(xx,2.18,.07)],.01,dark)
    for zz in [.3,1.95]:box('Timber door crosspiece',at(dc,zz,.09),(dw,.05,.09),wood,angle)
    box('Old stone door lintel',at(dc,2.3,.06),(dw+.3,.3,.18),stone,angle);box('Stone doorstep',at(dc,.1,.22),(dw+.4,.5,.2),stone,angle)
   for zf in balconies.get(BID,[]):
    zf*=h;bw=min(L*.32,3.1);cx=L*.8;depth=.75
    box('Estimated balcony slab',at(cx,zf,depth/2),(bw,depth,.16),trim,angle,.012)
    a0=cx-bw/2;a1=cx+bw/2
    for zz in [zf+.18,zf+.95]:line('Balcony horizontal railing',[at(a0,zz,depth),at(a1,zz,depth)],.025,metal)
    for xx in np.linspace(a0,a1,max(4,round(bw/.15))):line('Balcony baluster',[at(xx,zf+.12,depth),at(xx,zf+.95,depth)],.012,metal)
   line('Rainwater downpipe',[at(L-.18,.3,.11),at(L-.18,h+.2,.11)],.032,trim)
   for zz in np.arange(1,h,2.5):box('Pipe fixing clip',at(L-.18,zz,.11),(.12,.1,.03),metal,angle)
 if b['type'] in ('flat','solar'):
  tilematerial=roofmat;tilepose=None
  if 'roof_texture' in b and b['type']=='flat':tilematerial,tilepose=source_material(BID+' / visible roof paving',roofmat,b['roof_texture'])
  # Roof paving joints clipped to the true outline, not rectangular proxy caps.
  def inside(q):
   test=False;x,y=q
   for a0,a1 in zip(p,np.roll(p,-1,axis=0)):
    if ((a0[1]>y)!=(a1[1]>y)) and x<(a1[0]-a0[0])*(y-a0[1])/(a1[1]-a0[1])+a0[0]:test=not test
   return test
  for x in np.arange(p[:,0].min()+.25,p[:,0].max()-.2,.65):
   for y in np.arange(p[:,1].min()+.25,p[:,1].max()-.2,.65):
    if all(inside((x+dx,y+dy)) for dx in [-.31,.31] for dy in [-.31,.31]):
     o=box('Individual rooftop paving tile',(x,y,h+.04),(.63,.63,.045),tilematerial)
     if tilepose:project_uv(o,tilepose)
  if b['type']=='solar':
   pv=mat(BID+' / blue photovoltaic cells',(.035,.072,.11),.35,metal=.4);u=p[1]-p[0];L=np.linalg.norm(u);u/=L;v=p[-1]-p[0];D=np.linalg.norm(v);v/=D
   for x in np.arange(.45,L-1,1.12):
    for y in np.arange(.4,D-1,1.8):
     q=p[0]+u*(x+.5)+v*(y+.8);q[2]=h+.7;o=box('Photovoltaic module',q,(1.03,1.67,.065),pv,math.atan2(u[1],u[0]),.012)
     for xx in np.linspace(-.5,.5,7):line('PV cell separator',[q+u*xx-v*.8+[0,0,.04],q+u*xx+v*.8+[0,0,.04]],.004,steel)
 elif b['type']=='metal':
  slab('Blue sheet roof substrate',p,h+.05,.1,blue)
  u=p[1]-p[0];length=np.linalg.norm(u);u/=length;v=p[-1]-p[0]
  for d in np.arange(0,length,.19):q=p[0]+u*d;q[2]=h+.19;line('Raised standing sheet seam',[q,q+v],.018,blue)
 elif b['type']=='construction':
  for q in p:
   for dx,dy in [(-.08,-.08),(.08,-.08),(.08,.08),(-.08,.08)]:line('Exposed column reinforcement',[q+[dx,dy,-.3],q+[dx,dy,.8]],.012,metal)
 elif b['type']=='gable':
  rgb=np.array(b.get('roof_texture',{}).get('rgb',[.5,.35,.22]));rgb=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)*1.6;claytile=mat(BID+' / source sampled clay tile tone',np.clip(rgb,.035,.6).tolist(),noise=True)
  if len(p)!=4:raise RuntimeError('Gable roof needs a traced quadrilateral')
  q=p.copy();q[:,2]=h+.13
  if np.linalg.norm(q[1]-q[0])<np.linalg.norm(q[2]-q[1]):q=np.roll(q,1,axis=0)
  r0=(q[0]+q[3])/2;r1=(q[1]+q[2])/2;rise=min(1.8,max(.65,np.linalg.norm(q[3]-q[0])*.25));r0[2]+=rise;r1[2]+=rise
  mesh('Two real pitched roof planes',[*q,r0,r1],[(0,1,5,4),(3,4,5,2)],claytile)
  mesh('Masonry gable ends',[q[0],q[3],r0,q[1],r1,q[2]],[(0,1,2),(3,4,5)],wall)
  for a0,a1,b0,b1 in [(q[0],q[1],r0,r1),(q[3],q[2],r0,r1)]:
   width=np.linalg.norm(a1-a0);slope=np.linalg.norm(b0-a0)
   for f in np.linspace(0,1,max(3,round(slope/.26))):line('Overlapping clay tile course',[a0+(b0-a0)*f,a1+(b1-a1)*f],.023,claytile)
   for f in np.linspace(0,1,max(3,round(width/.21))):line('Individual curved clay tile roll',[a0+(a1-a0)*f,b0+(b1-b0)*f],.042,claytile)
  line('Capped clay ridge',[r0,r1],.11,claytile)
  for f in np.linspace(0,1,max(2,round(np.linalg.norm(r1-r0)/.3))):
   q0=r0+(r1-r0)*f;axis=(r1-r0)/np.linalg.norm(r1-r0);side=np.array([-axis[1],axis[0],0]);line('Ridge cap joint',[q0+side*.115*math.cos(v)+np.array([0,0,.115*math.sin(v)]) for v in np.linspace(0,math.pi,9)],.008,claytile)
 else:
  # Inset hip slopes follow this building's six-sided traced footprint.
  inner=cent+(p-cent)*.32;inner[:,2]=h+1.1
  for j in range(len(p)):
   k=(j+1)%len(p);a0=p[j]+[0,0,.15];a1=p[k]+[0,0,.15];b0=inner[j];b1=inner[k];mesh('Blue hipped roof slope',[a0,a1,b1,b0],[(0,1,2,3)],blueTile)
   for frac in np.arange(.08,1,.11):line('Overlapping tile course',[a0+(b0-a0)*frac,a1+(b1-a1)*frac],.019,blueTile)
   length=np.linalg.norm(a1-a0)
   for frac in np.arange(0,1,.25/max(length,.25)):line('Blue roof tile rib',[a0+(a1-a0)*frac,b0+(b1-b0)*frac],.016,blueTile)
   line('Hip ridge cap',[a0,b0],.065,blueTile)
  slab('Upper hip roof cap',inner,h+1.1,.06,blueTile)
 for fixture in [f for f in fixtures if f['building_id']==BID]:
  q=np.array(fixture['world_center'])-[0,0,BASE]
  if fixture['kind']=='tank':
   ob=cylinder('Source-located cylindrical rooftop fixture',q,.24,1.0,steel);ob['evidence']=fixture['evidence'];cylinder('Fixture lid',q+[0,0,.52],.26,.045,steel)
   for dx,dy in [(-.16,-.1),(.16,-.1),(0,.16)]:line('Fixture support leg',[q+[dx,dy,-.5],q+[dx*1.4,dy*1.4,-.7]],.024,steel)
   line('Estimated rooftop supply pipe',[q+[.24,0,0],q+[.43,0,0],q+[.43,0,-.7]],.018,trim)
  else:cylinder('Source-located roof vent',q,.18,.5,trim);cylinder('Vent cap',q+[0,0,.27],.23,.07,trim)
 C['opening_count']=opening_count;C['object_count']=len(C.objects);ledger.append(dict(id=BID,name=b['name'],objects=len(C.objects),openings=opening_count,roof_support=b['roof_support'],status='geometry generated; per-building comparison not yet accepted'))
 print('BUILD',BID,len(C.objects),opening_count,flush=True)
text=bpy.data.texts.new('ARCHITECTURE | acceptance ledger');text.write(json.dumps(ledger,ensure_ascii=False,indent=2));(OUT/'building_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2))
groundpath=ROOT/'work/buildings/ground_context.npz'
if groundpath.exists():
 for old in list(bpy.data.collections):
  if old.name.startswith('12 CONTEXT'):
   for ob in list(old.objects):bpy.data.objects.remove(ob,do_unlink=True)
   bpy.data.collections.remove(old)
 BASE=0;BID='SITE';C=bpy.data.collections.new('12 CONTEXT | estimated ground and source colours');s.collection.children.link(C);z=np.load(groundpath);gm=mat('Estimated terrain / unobserved earth',(.23,.25,.18),noise=True);o=mesh('Estimated continuous terrain',z['xyz'],z['faces'],gm);meta=json.loads((ROOT/'work/buildings/ground_context.json').read_text());o['status']=meta['status'];o['height_evidence']='Interpolated estimated architectural bases; not recovered ground.'
 for ts in meta['source_times']:
  pose=poses[str(ts)];m=gm.copy();m.name=f'Ground source {ts}s | baked illumination';tex=m.node_tree.nodes.new('ShaderNodeTexImage');source=ROOT/pose['source'];tex.image=bpy.data.images.load(str(source),check_existing=True);tex.extension='CLIP';p=m.node_tree.nodes.get('Principled BSDF');m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);o.data.materials.append(m)
 uv=o.data.uv_layers.new(name='Visible source on estimated ground')
 for face in o.data.polygons:
  face.material_index=int(z['material_ids'][face.index])
  for k,li in enumerate(face.loop_indices):uv.data[li].uv=z['uv'][face.index,k]
ca=json.loads((ROOT/'work/buildings/return_camera_roof_candidate.json').read_text());rc=bpy.data.cameras.new('Return 256s | manual roof controls');ro=bpy.data.objects.new(rc.name,rc);s.collection.objects.link(ro);rc.lens=ca['K'][0][0]*36/1600;rc.sensor_width=36;rc.clip_end=3000;M=np.eye(4);M[:3,:3]=np.array(ca['rotation_world_to_camera']).T@np.diag([1,-1,-1]);M[:3,3]=ca['position'];ro.matrix_world=Matrix(M);ro['status']='Manually calibrated reference camera; not registered SfM pose'
s['Reconstruction_status']=f'{len(ledger)} new architectural candidates; source comparisons and remaining village inventory pending. Not accepted as full-village completion.'
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_percentage=100
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.4
for name in ['Video 044.00s | recovered','Review | village oblique']:
 if name in bpy.data.objects:s.camera=bpy.data.objects[name];break
s.render.resolution_x=1600;s.render.resolution_y=900
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:im.pack()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Village_Building_Candidates.blend'),compress=True)
for name,cam in ([] if os.environ.get('SKIP_RENDER') else [('Architecture_44s','Video 044.00s | recovered'),('Architecture_Oblique','Review | village oblique'),('Architecture_Return_256s',ro.name)]):
 s.camera=bpy.data.objects[cam];s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('ARCHITECTURE_CANDIDATES_SAVED',flush=True)
