"""Rectangular, source-refined village architecture with real facade and roof details.

Geometry is accumulated directly into editable material groups; each independent
component and polygon range is retained. No skewed residential core is permitted.
"""
import bpy,math,json,os,hashlib,copy
from mathutils.geometry import tessellate_polygon
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parent.parent;SPEC=ROOT/'source/inventory.json';PROFILES=json.loads((ROOT/'source/profiles.json').read_text());OUT=ROOT/os.environ.get('ARCHITECTURE_OUT','rebuild');OUT.mkdir(parents=True,exist_ok=True);DATA=json.loads(SPEC.read_text())['buildings'];SELECT=set(filter(None,os.environ.get('BUILD_IDS','').split(',')))
if SELECT:DATA=[b for b in DATA if b['id'] in SELECT]
s=bpy.context.scene;old=[c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE')];remove=[]
partial=bool(SELECT and os.environ.get('KEEP_EXISTING'))
for parent in old:
 for c in list(parent.children):
  if not partial or c.name.split(' | ')[0] in SELECT:remove.extend(c.objects);remove.append(c)
 if not partial:remove.append(parent)
if remove:bpy.data.batch_remove(ids=remove)
PARENT=old[0] if partial and old else bpy.data.collections.new('11 ARCHITECTURE | orthogonal multiview buildings')
if PARENT.name not in s.collection.children:s.collection.children.link(PARENT)
def linear(rgb):
 a=np.array(rgb,dtype=float);return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def material(name,rgb,rough=.8,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*linear(rgb),1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*linear(rgb),1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;return m
WHITE=material('V3 / weathered ivory architectural trim',[.77,.77,.71]);DARK=material('V3 / deep reveal shadow',[.055,.060,.052]);FRAME=material('V3 / aged aluminium frames',[.20,.23,.22],.42,.55);STEEL=material('V3 / stainless tank and bracing',[.60,.64,.64],.30,.78);RUST=material('V3 / oxidized roof bracing',[.29,.26,.21],.73,.35);GLASS=material('V3 / dark green reflective glazing',[.29,.36,.33],.31,.16);WOOD=material('V3 / aged timber doors',[.28,.215,.14],.85);MORTAR=material('V3 / worn concrete plinth',[.44,.45,.40]);SOLAR=material('V3 / photovoltaic cells',[.11,.17,.22],.28,.45);BLUE=material('V3 / painted sheet roof',[.17,.49,.61],.52,.25)
def weather_material(name,color,style,age,axis=0,H=10,stains=None,wall_length=10):
 m=material(name,color,.86);nt=m.node_tree;N=nt.nodes;L=nt.links;bs=N.get('Principled BSDF');tex=N.new('ShaderNodeTexCoord');sep=N.new('ShaderNodeSeparateXYZ');L.new(tex.outputs['Object'],sep.inputs[0]);coord=N.new('ShaderNodeCombineXYZ');L.new(sep.outputs['X' if axis in (0,2) else 'Y'],coord.inputs['X']);L.new(sep.outputs['Y' if axis==2 else 'Z'],coord.inputs['Y']);rgb=linear(color)
 def mathnode(op,a=None,b=None):
  n=N.new('ShaderNodeMath');n.operation=op
  for i,x in enumerate([a,b]):
   if x is None:continue
   if isinstance(x,(int,float)):n.inputs[i].default_value=x
   else:L.new(x,n.inputs[i])
  return n.outputs[0]
 grain=N.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=62;grain.inputs['Detail'].default_value=3;L.new(coord.outputs[0],grain.inputs['Vector'])
 macro=N.new('ShaderNodeTexNoise');macro.inputs['Scale'].default_value=.75;macro.inputs['Detail'].default_value=4;L.new(coord.outputs[0],macro.inputs['Vector']);patch=N.new('ShaderNodeValToRGB');patch.color_ramp.elements[0].position=.38;patch.color_ramp.elements[1].position=.66;L.new(macro.outputs['Fac'],patch.inputs[0])
 stretch=N.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(3.2,.17,1);L.new(coord.outputs[0],stretch.inputs[0]);streak=N.new('ShaderNodeTexNoise');streak.inputs['Scale'].default_value=1;streak.inputs['Detail'].default_value=3;L.new(stretch.outputs[0],streak.inputs['Vector'])
 base=mathnode('MAXIMUM',mathnode('SUBTRACT',1,mathnode('DIVIDE',sep.outputs['Z'],1.8)),0);rim=mathnode('MAXIMUM',mathnode('SUBTRACT',1,mathnode('DIVIDE',mathnode('SUBTRACT',H,sep.outputs['Z']),1.55)),0);wet=mathnode('MINIMUM',mathnode('ADD',base,rim),1)
 dirt=mathnode('MULTIPLY',mathnode('ADD',mathnode('MULTIPLY',patch.outputs['Color'],.22),mathnode('MULTIPLY',streak.outputs['Fac'],wet)),age)
 if stains:
  for stain in stains:
   xx=mathnode('DIVIDE',mathnode('SUBTRACT',sep.outputs['X' if axis==0 else 'Y'],stain['x']*wall_length),stain['rx']*wall_length);zz=mathnode('DIVIDE',mathnode('SUBTRACT',sep.outputs['Z'],stain['z']*H),stain['rz']*H);radius=mathnode('ADD',mathnode('MULTIPLY',xx,xx),mathnode('MULTIPLY',zz,zz));zone=mathnode('MAXIMUM',mathnode('SUBTRACT',1,radius),0);speckle=mathnode('MULTIPLY',patch.outputs['Color'],stain['strength']*1.1);dirt=mathnode('MINIMUM',mathnode('ADD',dirt,mathnode('MULTIPLY',zone,speckle)),.92)
 if style in ('ceramic','ceramic_horizontal','brick'):
  tiles=N.new('ShaderNodeTexBrick');tiles.inputs['Scale'].default_value=1;tiles.inputs['Brick Width'].default_value=.235 if style=='brick' else (.30 if style=='ceramic_horizontal' else .10);tiles.inputs['Row Height'].default_value=.075 if style=='brick' else (.095 if style=='ceramic_horizontal' else .20);tiles.inputs['Mortar Size'].default_value=.004 if style=='brick' else .0011;tiles.offset=.5 if style=='brick' else 0;tiles.inputs['Color1'].default_value=(*(rgb*.96),1);tiles.inputs['Color2'].default_value=(*(rgb*1.03),1);tiles.inputs['Mortar'].default_value=(*(rgb*.78),1);L.new(coord.outputs[0],tiles.inputs['Vector']);surface=tiles.outputs['Color'];bumpheight=tiles.outputs['Fac']
 else:
  tint=N.new('ShaderNodeValToRGB');tint.color_ramp.elements[0].color=(*(rgb*.91),1);tint.color_ramp.elements[1].color=(*(rgb*1.04),1);L.new(grain.outputs['Fac'],tint.inputs[0]);surface=tint.outputs['Color'];bumpheight=grain.outputs['Fac']
 mix=N.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(*linear([.42,.44,.40]),1);L.new(dirt,mix.inputs[0]);L.new(surface,mix.inputs[1]);L.new(mix.outputs[0],bs.inputs['Base Color']);bump=N.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.27;bump.inputs['Distance'].default_value=.009 if style=='brick' else .003;L.new(bumpheight,bump.inputs['Height']);L.new(bump.outputs[0],bs.inputs['Normal']);m['appearance_evidence']='Source-family colour; procedural tile/grain, low-frequency patches, base moisture and parapet runoff are inferred continuous finish.';return m
class Builder:
 def __init__(self,b):
  self.b=b;self.id=b['id'];self.W=b['rectangle']['width'];self.D=b['rectangle']['depth'];self.H=b['roof_height']-b['base_height'];self.poly=np.array(b.get('plan_polygon',[[0,0],[1,0],[1,1],[0,1]]),float)*[self.W,self.D];self.groups={};self.curves={};self.col=bpy.data.collections.new(self.id+' | '+b['name']);PARENT.children.link(self.col);theta=b['rectangle']['angle_radians'];q=b['roof_world'][0];self.matrix=Matrix.Translation(Vector((q[0],q[1],b['base_height'])))@Matrix.Rotation(theta,4,'Z');self.components=0;self.openings=0
 def mesh(self,name,verts,faces,mat,smooth=False):
  if len(self.poly)>4 and name=='Individual source hexagonal terrace paver' and not all(self.inside(v[0],v[1]) for v in verts):return
  key=(mat.name,smooth);g=self.groups.setdefault(key,dict(material=mat,verts=[],faces=[],components=[]));offset=len(g['verts']);start=len(g['faces']);g['verts'].extend([tuple(v) for v in verts]);g['faces'].extend([tuple(offset+i for i in f) for f in faces]);g['components'].append(dict(name=self.id+' / '+name,first_polygon=start,polygon_count=len(faces)));self.components+=1
 def inside(self,x,y):
  inside=False
  for a,b in zip(self.poly,np.roll(self.poly,-1,axis=0)):
   if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
  return inside
 def slab(self,name,z,thickness,mat):
  edges=np.roll(self.poly,-1,axis=0)-self.poly;normals=np.column_stack([edges[:,1],-edges[:,0]])/np.linalg.norm(edges,axis=1)[:,None];outline=self.poly-.01*(normals+np.roll(normals,1,axis=0));pts=[Vector((x,y,0)) for x,y in outline];n=len(pts);v=[(x,y,z+dz) for dz in [-thickness/2,thickness/2] for x,y in outline];tri=tessellate_polygon([pts]);faces=[]
  for t in tri:
   ids=[(int(q) if isinstance(q,int) else min(range(n),key=lambda i:(pts[i]-q).length)) for q in t];faces.extend([tuple(reversed(ids)),tuple(i+n for i in ids)])
  faces.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
  self.mesh(name,v,faces,mat)
 def clipped_box(self,name,center,dims,mat):
  cx,cy,cz=center;ww,dd,hh=dims;x0,x1=cx-ww/2,cx+ww/2;y0,y1=cy-dd/2,cy+dd/2
  xs=sorted(set([x0,x1]+[float(x) for x,y in self.poly if x0<x<x1]));ys=sorted(set([y0,y1]+[float(y) for x,y in self.poly if y0<y<y1]))
  for a,b in zip(xs,xs[1:]):
   for c,d in zip(ys,ys[1:]):
    if self.inside((a+b)/2,(c+d)/2):self.box(name+' clipped',((a+b)/2,(c+d)/2,cz),(b-a,d-c,hh),mat)
 def box(self,name,center,dims,mat,basis=None,open_ends=()):
  if len(self.poly)>4 and basis is None and name in ('Distinct source roof finish zone','Source dark waterproof repair patch','Source-inspired roof repair paver'):
   self.clipped_box(name,center,dims,mat);return
  h=np.array(dims)/2;v=np.array([[-1,-1,-1],[-1,-1,1],[-1,1,-1],[-1,1,1],[1,-1,-1],[1,-1,1],[1,1,-1],[1,1,1]])*h
  if basis is not None:v=v@np.array(basis)
  v+=center;faces=[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)]
  faces=[f for i,f in enumerate(faces) if not (i==4 and 'start' in open_ends) and not (i==5 and 'end' in open_ends)]
  if basis is not None and np.linalg.det(np.array(basis))<0:faces=[tuple(reversed(f)) for f in faces]
  self.mesh(name,v,faces,mat)
 def line(self,name,points,r,mat):
  if len(self.poly)>4 and name in ('Roof slab expansion joint','Roof slab transverse joint'):
   a,z=np.array(points[0]),np.array(points[-1]);ts=sorted(set([0.,1.]+[float((v[k]-a[k])/(z[k]-a[k])) for v in self.poly for k in [0,1] if abs(z[k]-a[k])>1e-8 and 0<(v[k]-a[k])/(z[k]-a[k])<1]))
   for t0,t1 in zip(ts,ts[1:]):
    mid=a+(z-a)*(t0+t1)/2
    if self.inside(*mid[:2]):self.line(name+' clipped',[a+(z-a)*t0,a+(z-a)*t1],r,mat)
   return
  key=(mat.name,round(r,5));g=self.curves.setdefault(key,dict(material=mat,r=r,items=[]));g['items'].append((name,[tuple(p) for p in points]));self.components+=1
 def cylinder(self,name,center,r,h,mat,n=16):
  cx,cy,cz=center;v=[(cx+r*math.cos(i*2*math.pi/n),cy+r*math.sin(i*2*math.pi/n),cz+z) for z in [-h/2,h/2] for i in range(n)];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];self.mesh(name,v,f,mat)
 def finish(self):
  for index,((matname,smooth),g) in enumerate(self.groups.items()):
   me=bpy.data.meshes.new(self.id+f' / editable mesh {index:02}');me.from_pydata(g['verts'],[],g['faces']);me.update();me.materials.append(g['material']);me.polygons.foreach_set('use_smooth',np.full(len(me.polygons),smooth,bool));ob=bpy.data.objects.new(me.name,me);self.col.objects.link(ob);ob.matrix_world=self.matrix;ob['building_id']=self.id;ob['original_components']=json.dumps(g['components'],ensure_ascii=False);ob['editing']='Select Linked in Edit Mode for independent real geometric components.'
  for index,(key,g) in enumerate(self.curves.items()):
   cu=bpy.data.curves.new(self.id+f' / editable curves {index:02}','CURVE');cu.dimensions='3D';cu.bevel_depth=g['r'];cu.bevel_resolution=1;cu.materials.append(g['material']);names=[]
   for name,pts in g['items']:
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for point,co in zip(sp.points,pts):point.co=(*co,1)
    names.append(self.id+' / '+name)
   ob=bpy.data.objects.new(cu.name,cu);self.col.objects.link(ob);ob.matrix_world=self.matrix;ob['building_id']=self.id;ob['original_components']=json.dumps(names,ensure_ascii=False)
  self.col['opening_count']=self.openings;self.col['source_frame_seconds']=self.b['t'];self.col['rectangular_core']=len(self.poly)==4;self.col['orthogonal_plan']=True;self.col['local_plan_polygon']=json.dumps(self.poly.tolist());self.col['width']=self.W;self.col['depth']=self.D;self.col['roof_height']=self.b['roof_height'];self.col['estimated_ground_height']=self.b['base_height'];self.col['original_component_count']=self.components;self.col['status']='Orthogonal multiview refinement; hidden details estimated';return dict(id=self.id,objects=len(self.col.objects),components=self.components,vertices=sum(len(o.data.vertices) for o in self.col.objects if o.type=='MESH'),openings=self.openings)

def make_building(b):
 B=Builder(b);p=PROFILES[b['id']];W,D,H=B.W,B.D,B.H;trim=material(b['id']+' / restrained facade trim',p['trim_color']);n=b['floors'];sh=H/n;seed=int(hashlib.sha256(b['id'].encode()).hexdigest()[:8],16);rng=np.random.default_rng(seed);wallmats=[weather_material(b['id']+f' / facade {j} {f["style"]}',f['color'],f['style'],f['age'],j%2,H,f.get('stains'),[W,D,W,D][j]) for j,f in enumerate(p['facades'])];roofmat=weather_material(b['id']+' / weathered roof finish',p['roof_color'],'paint',p.get('roof_age',.17),2,H);parapet=weather_material(b['id']+' / stained parapet concrete',[.73,.74,.68],'aged_plaster',.65,0,H+.5);wood=weather_material(b['id']+' / timber grain',[.34,.27,.17],'aged_plaster',.18,0,2.2)
 accent=material(b['id']+' / source burgundy trim',p['accent_color']) if p.get('accent_color') else trim
 glass=material(b['id']+' / source green glazing',p['glazing_color'],.26,.25) if p.get('glazing_color') else GLASS
 B.slab('Ground floor orthogonal slab',.08,.16,MORTAR)
 for floor in range(1,n+1):
  if b['type']!='construction':B.slab('Structural floor slab',floor*sh-.10+(.026 if floor==n else 0),.2,roofmat)
 corners=np.column_stack([B.poly,np.zeros(len(B.poly))])
 for segment,(a,z) in enumerate(zip(corners,np.roll(corners,-1,axis=0))):
  delta=z-a;j=(0 if delta[0]>0 else 2) if abs(delta[0])>1e-6 else (1 if delta[1]>0 else 3)
  u=z-a;L=np.linalg.norm(u);u/=L;out=np.array([u[1],-u[0],0]);basis=np.array([u,out,[0,0,1]]);f=copy.deepcopy(p['facades'][j]);wm=wallmats[j]
  fullL=[W,D,W,D][j];u0=[a[0],a[1],W-a[0],D-a[1]][j]
  f['windows']=[dict(w,x=(w['x']*fullL-u0)/L) for w in f['windows'] if u0+.15<w['x']*fullL<u0+L-.15]
  f['loggias']=[dict(log,x0=max(0,(log['x0']*fullL-u0)/L),x1=min(1,(log['x1']*fullL-u0)/L)) for log in f.get('loggias',[]) if log['x1']*fullL>u0 and log['x0']*fullL<u0+L]
  def at(x,zz,depth=0):return a+u*x+out*depth+[0,0,zz]
  def box(name,x,zz,ww,hh,depth,thickness,mat,open_ends=()):B.box(name,at(x,zz,depth),(ww,thickness,hh),mat,basis,open_ends)
  holes=[];loggias=[]
  for log in f.get('loggias',[]):
   for floor in log['floors']:
    if floor>=n:continue
    x0=max(.18,log['x0']*L);x1=min(L-.18,log['x1']*L);z0=floor*sh+.10;z1=(floor+1)*sh-.25
    if x1-x0<1.1:continue
    holes.append([x0,x1,z0,z1,'loggia']);loggias.append((x0,x1,z0,z1,log))
  for w in f['windows']:
   ww=min(w['width'],L*.62);hh=min(w['height'],sh*.76);cx=w['x']*L;cz=w['z']*H;x0=max(.18,cx-ww/2);x1=min(L-.18,cx+ww/2);z0=max(.32,cz-hh/2);z1=min(H-.34,cz+hh/2)
   if x1-x0<.45 or z1-z0<.4:continue
   if any(x0<r and x1>l and z0<t and z1>bt for l,r,bt,t,k in holes):continue
   holes.append([x0,x1,z0,z1,'window'])
  if j==0 and abs(a[1])<1e-6 and L>2.1 and not p.get('no_inferred_door') and not b.get('public_hall'):
   dw=min(1.35,L*.23);cx=L*.47;door=[cx-dw/2,cx+dw/2,.13,min(2.35,sh-.2),'door'];holes=[v for v in holes if not(v[0]<door[1] and v[1]>door[0] and v[2]<door[3] and v[3]>door[2])];holes.append(door)
  if b.get('public_hall') and j==0:holes=[[L*.13,L*.87,.12,H*.85,'hall']]
  xs=sorted(set([0,L]+[q for h0 in holes for q in h0[:2]]));zs=sorted(set([0,H]+[q for h0 in holes for q in h0[2:4]]))
  for x0,x1 in zip(xs[:-1],xs[1:]):
   for z0,z1 in zip(zs[:-1],zs[1:]):
    if any(l<(x0+x1)/2<r and bt<(z0+z1)/2<t for l,r,bt,t,k in holes):continue
    box('Wall panel with true opening',(x0+x1)/2,(z0+z1)/2,x1-x0,z1-z0,-.12,.24,wm,tuple(v for v,yes in [('start',abs(x0)<1e-6),('end',abs(x1-L)<1e-6)] if yes))
  for x0,x1,z0,z1,kind in holes:
   B.openings+=1;cx=(x0+x1)/2;cz=(z0+z1)/2;ww=x1-x0;hh=z1-z0
   if b['type']=='construction' or p.get('unfinished') or kind in ('loggia','hall'):continue
   if kind=='door':
    box('Recessed entrance door',cx,cz,ww-.08,hh,-.10,.08,wood);box('Door threshold',cx,.11,ww+.25,.18,.14,.60,MORTAR)
    for frac in np.linspace(-.42,.42,7):B.line('Timber door plank joint',[at(cx+ww*frac,z0+.04,-.05),at(cx+ww*frac,z1-.04,-.05)],.009,DARK)
    B.line('Entrance metal pull handle',[at(cx+ww*.32,.96,.02),at(cx+ww*.32,1.29,.02)],.016,STEEL)
   else:
    recess=next((q['depth'] for q in f.get('accent_recesses',[]) if abs(q['x']*L-cx)<.3 and abs(q['z']*H-cz)<.4),.13)
    box('Deep window reveal shadow',cx,cz,ww,hh,-recess-.12,.035,DARK)
    gx0,gx1,gz0,gz1=x0,x1,z0,z1
    if recess>.20:
     box('Source alcove plaster back wall',cx,cz,ww,hh,-recess-.035,.045,wm);gx0=cx+ww*.03;gx1=cx+ww*.39;gz0=cz-hh*.28;gz1=cz+hh*.39
    box('Recessed glazing',(gx0+gx1)/2,(gz0+gz1)/2,gx1-gx0-.08,gz1-gz0-.08,-recess,.028,glass)
    if recess>.20:
     for xx in [x0,x1]:B.box('Deep window reveal return',at(xx,cz,-recess/2),(.08,recess,hh),wm,basis)
     B.box('Deep recessed window sill',at(cx,z0-.03,-recess/2),(ww,recess,.09),trim,basis)
    for xx in [gx0,(gx0+gx1)/2,gx1]:box('Window vertical aluminium frame',xx,(gz0+gz1)/2,.055,gz1-gz0,-recess+.075,.09,FRAME)
    for zz in [gz0,gz1,(gz0+gz1)/2+.20*(gz1-gz0)]:box('Window horizontal aluminium frame',(gx0+gx1)/2,zz,gx1-gx0,.045,-recess+.075,.09,FRAME)
    if b['type']!='gable' and recess<=.20:
     for xx in np.arange(x0+.13,x1-.06,.17):B.line('Window security vertical bar',[at(xx,z0+.05,.11),at(xx,z1-.05,.11)],.011,FRAME)
     for zz in [cz-.25*hh,cz+.22*hh]:B.line('Window security crossbar',[at(x0+.04,zz,.11),at(x1-.04,zz,.11)],.011,FRAME)
    box('Projecting stone window sill',cx,z0-.055,ww+.12,.065,.045,.27,trim)
   for xx in [x0-.045,x1+.045]:box('Window or door outer vertical reveal',xx,cz,.045,hh+.07,.01,.055,trim if p['style']!='brick' else MORTAR)
   box('Window or door head lintel',cx,z1+.04,ww+.11,.055,.01,.065,trim if p['style']!='brick' else MORTAR)
  for x0,x1,z0,z1,log in loggias:
   dep=log['depth'];cx=(x0+x1)/2;ww=x1-x0;hh=z1-z0;box('Recessed balcony rear wall',cx,(z0+z1)/2,ww,hh,-dep,.20,wm);box('Balcony tiled floor',cx,z0-.02,ww,.13,-dep/2,dep+.16,roofmat)
   for xx in [x0,x1]:B.box('Balcony side return',at(xx,(z0+z1)/2,-dep/2),(.17,dep,hh),wm,basis)
   doorw=min(1.3,ww*.26);box('Balcony inset sliding door shadow',cx,(z0+z1)/2,doorw,hh*.86,-dep+.11,.03,DARK);box('Balcony inset sliding glass',cx,(z0+z1)/2,doorw-.10,hh*.82,-dep+.14,.04,glass)
   for xx in [cx-doorw/2,cx,cx+doorw/2]:box('Balcony rear door frame',xx,(z0+z1)/2,.045,hh*.86,-dep+.18,.06,FRAME)
   for xx in np.linspace(x0,x1,log.get('columns',2)):
    box('Straight balcony supporting column',xx,(z0+z1)/2,.20,hh,.015,.24,trim);box('Balcony column capital',xx,z1-.08,.34,.16,.015,.36,trim);box('Balcony column foot',xx,z0+.12,.29,.22,.015,.30,trim)
   if log.get('arched'):
    positions=np.linspace(x0,x1,25);verts=[]
    for xx in positions:
     drop=.10+.32*(abs((xx-cx)/(ww/2))**2);verts.extend([at(xx,z1,.07),at(xx,z1-drop,.07)])
    B.mesh('Shallow curved balcony soffit',verts,[(2*k,2*k+1,2*k+3,2*k+2) for k in range(24)],trim)
   railz=z0+.96
   if p['baluster']=='stone':
    box('Stone balcony rail coping',cx,railz,ww+.14,.13,.055,.22,accent);box('Stone balcony rail foot',cx,z0+.15,ww,.15,.04,.22,trim)
    for xx in np.arange(x0+.20,x1-.12,.24):
     # Turned profiles give actual baluster silhouettes, not printed railing stripes.
     for lo,hi,rad in [(.22,.35,.052),(.35,.48,.034),(.48,.66,.056),(.66,.81,.033),(.81,.90,.052)]:B.cylinder('Turned concrete balcony baluster',at(xx,z0+(lo+hi)/2,.05),rad,hi-lo,trim,12)
   else:
    for zz in [z0+.18,railz]:B.line('Balcony metal horizontal handrail',[at(x0,zz,.06),at(x1,zz,.06)],.025,FRAME)
    for xx in np.arange(x0+.12,x1,.14):B.line('Balcony vertical baluster',[at(xx,z0+.18,.06),at(xx,railz,.06)],.014,FRAME)
  if p.get('concrete_frame'):
   for xx in [.14,L-.14]:box('Exposed structural concrete column',xx,H/2,.28,H,.02,.30,MORTAR)
  if b['type']!='gable':
   for floor in (range(1,n) if p.get('concrete_frame') or p.get('storey_bands') else []):
    box('Storey band projecting coping',L/2,floor*sh,L,(.24 if p.get('unfinished') else .065),.015,(.26 if p.get('unfinished') else .06),trim if p['style']!='brick' else MORTAR)
   box('Ground damp plinth',L/2,.22,L,.44,.018,.09,MORTAR)
  if b['type'] in ('flat','solar','metal','hip') and not p.get('unfinished'):
   levels=[(0,.20,.09),(.10,.27,.07)] if p['cornice']=='double' else [(-.09,.17,.07),(0,.24,.09),(.09,.30,.06)]
   for dz,th,hh in levels:box('Layered roof cornice',L/2,H+dz,L+.16,hh,.03,th,trim)
   if p['cornice']=='dark_band':box('Dark roof fascia band',L/2,H-.24,L,.10,.03,.27,FRAME)
  if b['type'] in ('flat','solar') and not p.get('unfinished'):
   box('Weathered roof parapet',L/2,H+.23,L,.46,-.03,.19,parapet);box('Pale parapet cap',L/2,H+.50,L+.06,.065,-.025,.27,trim)
  # Drainage follows a real wall corner; repeated brackets and outlet bend are editable.
  if j in (0,2):
   xx=L-.19;B.line('Rainwater downpipe',[at(xx,H+.22,.15),at(xx,.35,.15),at(xx,.23,.30)],.040,trim)
   for zz in np.arange(.8,H,1.65):box('Rainwater pipe fixing bracket',xx,zz,.16,.045,.16,.10,FRAME)
  if p.get('accent_color'):box('Source coloured roof fascia',L/2,H-.24,L,.12,.03,.27,accent)
  acs=[dict(x,x=(x['x']*fullL-u0)/L) for x in p.get('ac_windows',[]) if x['edge']==j and u0+.45<x['x']*fullL<u0+L-.45]
  if not acs and b['type'] not in ('gable','construction') and not p.get('unfinished') and L>5 and j==0:acs=[dict(x=.16,z=((n-1)*sh+.50)/H)]
  for ac in acs:
   cx=ac['x']*L;cz=max(.8,ac['z']*H)
   if any(cx-.44<r and cx+.44>l and cz-.30<t and cz+.30>bt for l,r,bt,t,k in holes):continue
   box('Exterior air conditioner housing',cx,cz,.78,.55,.26,.43,trim)
   for xx in np.linspace(cx-.23,cx+.23,10):B.line('Condenser front grille',[at(xx,cz-.18,.49),at(xx,cz+.18,.49)],.009,FRAME)
   for xx in [cx-.28,cx+.28]:B.line('Air conditioner support angle',[at(xx,cz-.27,.49),at(xx,cz-.27,.06),at(xx,cz+.03,.06)],.02,FRAME)
   B.line('Air conditioner cable and drain',[at(cx+.39,cz,.25),at(cx+.55,cz-.1,.18),at(cx+.55,cz-.95,.15)],.016,trim)
 if p.get('terrace_canopy'):
  c=p['terrace_canopy'];x0,x1=c['x0']*W,c['x1']*W;y0,y1=c['y0']*D,c['y1']*D;ch=c['height'];cm=material(b['id']+' / pale blue terrace canopy',c['color'],.65,.18)
  for x in [x0,x1]:
   for y in [y0,y1]:B.box('Canopy steel post',(x,y,H+ch/2),(.075,.075,ch),FRAME)
  B.box('Raised terrace canopy sheet',((x0+x1)/2,(y0+y1)/2,H+ch),(x1-x0+.2,y1-y0+.2,.06),cm)
  for x in np.arange(x0,x1,.22):B.line('Canopy folded seam',[(x,y0-.1,H+ch+.045),(x,y1+.1,H+ch+.045)],.015,cm)
 # Roof finish and equipment.
 if b['type'] in ('flat','solar'):
  if p.get('roof_pavers')=='hex':
   tiles=[material(b['id']+f' / hexagonal roof paver {i}',np.clip(np.array(p['roof_color'])*f,.1,.95)) for i,f in enumerate([.94,.98,1.02,1.055])];radius=.255
   for row,y in enumerate(np.arange(.45,D-.35,radius*1.5)):
    for x in np.arange(.45+row%2*radius*.866,W-.35,radius*1.732):
     verts=[(x+radius*.97*math.cos(a),y+radius*.97*math.sin(a),H+.041) for a in np.linspace(math.pi/6,2*math.pi+math.pi/6,6,endpoint=False)];B.mesh('Individual source hexagonal terrace paver',verts,[(0,1,2,3,4,5)],tiles[int(rng.integers(4))])
   repair=weather_material(b['id']+' / dark roof waterproof repair',[.26,.28,.25],'paint',.6,2,H);B.box('Source dark waterproof repair patch',(W*.35,D*.80,H+.052),(W*.5,D*.26,.016),repair)
  if p.get('roof_patchwork'):
   patch=weather_material(b['id']+' / pale replacement roof pavers',[.82,.81,.74],'paint',.32,2,H)
   for ix,x in enumerate(np.arange(.35,W-.6,.95)):
    for iy,y in enumerate(np.arange(.35,D-.6,.95)):
     if (ix+2*iy)%5 in [0,1]:B.box('Source-inspired roof repair paver',(x+.42,y+.42,H+.022),(.83,.83,.025),patch)
  for zone in p.get('roof_zones',[]):
   zm=weather_material(b['id']+' / source roof colour zone',zone['color'],'paint',.17,2,H);y0=zone['y0']*D;y1=zone['y1']*D;B.box('Distinct source roof finish zone',(W/2,(y0+y1)/2,H+.017),(W-.28,y1-y0,.024),zm)
  # Low-contrast slab joints and individual repair pieces, with uneven aged patches in the material.
  for x in np.arange(.65,W-.4,.85):B.line('Roof slab expansion joint',[(x,.2,H+.025),(x,D-.2,H+.025)],.003,roofmat)
  for y in np.arange(.65,D-.4,.85):B.line('Roof slab transverse joint',[(.2,y,H+.025),(W-.2,y,H+.025)],.003,roofmat)
  B.box('Roof drain grating',(W-.40,D-.42,H+.04),(.24,.24,.045),FRAME)
  for y in np.linspace(D-.50,D-.34,5):B.line('Drain grate slot',[(W-.51,y,H+.065),(W-.29,y,H+.065)],.008,DARK)
  if p.get('roof_partition'):
   y=D*p['roof_partition'];B.box('Source roof terrace dividing parapet',(W/2,y,H+.27),(W-.26,.18,.54),parapet);B.box('Terrace divider cap',(W/2,y,H+.56),(W-.20,.25,.07),trim)
  if b['type']=='solar':
   for x in np.arange(.40,W-1.10,1.15):
    for y in np.arange(.45,D-1.85,1.90):
     elev=H+.85;B.box('Photovoltaic module',(x+.52,y+.85,elev),(1.06,1.73,.07),SOLAR)
     for xx in [x,x+1.04]:B.line('PV aluminium support rail',[(xx,y,elev+.045),(xx,y+1.72,elev+.045)],.02,STEEL)
     for yy in [y,y+1.72]:B.line('PV short frame rail',[(x,yy,elev+.045),(x+1.04,yy,elev+.045)],.02,STEEL)
     for xx in np.linspace(x+.17,x+.88,5):B.line('Photovoltaic cell separator',[(xx,y+.02,elev+.043),(xx,y+1.70,elev+.043)],.004,STEEL)
     for dx in [.15,.88]:B.line('Photovoltaic supporting leg',[(x+dx,y+.30,H+.10),(x+dx,y+.30,elev-.04)],.027,FRAME)
 elif b['type']=='metal':
  metalroof=weather_material(b['id']+' / faded painted sheet roof',p['roof_color'] if np.mean(p['roof_color'])<.80 else [.50,.57,.57],'paint',.18,2,H)
  B.box('Closed standing seam roof substrate',(W/2,D/2,H+.06),(W+.16,D+.16,.12),metalroof)
  for x in np.arange(.10,W,.22):B.line('Standing roof seam',[(x,-.07,H+.14),(x,D+.07,H+.14)],.023,metalroof)
 elif b['type']=='construction':
  for x,y,_ in corners:
   for dx,dy in [(-.06,-.06),(-.06,.06),(.06,-.06),(.06,.06)]:B.line('Exposed column reinforcement',[(x+dx,y+dy,H-.15),(x+dx,y+dy,H+.85)],.013,RUST)
 elif b['type']=='gable':
  # Individual overlapping curved clay tiles, with per-tile colour variation and worn edges.
  for a,z in zip(corners,np.roll(corners,-1,axis=0)):B.line('Timber bearing plate closes eave gap',[a+[0,0,H+.055],z+[0,0,H+.055]],.09,wood)
  along_x=b.get('gable_ridge_axis','x' if W>=D else 'y')=='x';length=W if along_x else D;depth=D if along_x else W;rise=min(2.0,max(.65,depth*.24));col=np.array(p['roof_color']);variants=[weather_material(b['id']+f' / aged clay tile {i}',np.clip(col*f,.13,.9).tolist(),'paint',.15,2,H) for i,f in enumerate([.90,.95,1.0,1.035,1.065])];under=material(b['id']+' / dark roof underlay',[.28,.25,.21]);ridge_axis=np.array([1,0,0]) if along_x else np.array([0,1,0]);cross_axis=np.array([0,1,0]) if along_x else np.array([1,0,0]);origin=np.array([0,0,H+.13]);eave=-.28;half=depth/2+.28
  for side in [0,1]:
   y0=eave if side==0 else depth+.28;sgn=1 if side==0 else -1;run=depth/2+.28;slopevec=cross_axis*sgn+np.array([0,0,rise/run]);slopevec/=np.linalg.norm(slopevec);normal=np.cross(ridge_axis,slopevec);normal*=1 if normal[2]>0 else -1;slopelen=np.sqrt(run*run+rise*rise);start=origin+cross_axis*y0
   v=[start+ridge_axis*(-.27),start+ridge_axis*(length+.27),start+ridge_axis*(length+.27)+slopevec*slopelen,start-ridge_axis*.27+slopevec*slopelen];B.mesh('Continuous pitched roof substrate',v,[(0,1,2,3)],under)
   if p.get('roof_surface')=='metal':
    B.mesh('Source red metal pitched roof',v,[(0,1,2,3)],roofmat)
    for x in np.arange(-.27,length+.25,.23):B.line('Standing roof seam on pitch',[start+ridge_axis*x+normal*.025,start+ridge_axis*x+slopevec*slopelen+normal*.025],.022,roofmat)
    continue
   spacing=.22;rowstep=.32
   for row,t in enumerate(np.arange(0,slopelen-.01,rowstep)):
    tilelen=min(.38,slopelen-t+.04)
    for idx,x in enumerate(np.arange(-.27,length+.25,spacing)):
     tw=min(spacing+.025,length+.30-x);v=[]
     for yy in [0,tilelen]:
      for xx in np.linspace(0,tw,7):v.append(start+ridge_axis*(x+xx)+slopevec*(t+yy)+normal*(.040*np.sin(np.pi*xx/tw)+.025))
     mat=variants[int(rng.choice(len(variants),p=[.10,.18,.37,.25,.10]))];B.mesh('Individual overlapping curved clay tile',v,[(k,k+1,k+8,k+7) for k in range(6)],mat)
   B.line('Timber roof eave fascia',[start-ridge_axis*.29,start+ridge_axis*(length+.29)],.065,wood)
  r0=origin+cross_axis*(depth/2)+[0,0,rise];r1=r0+ridge_axis*length
  for x in np.arange(-.25,length+.2,.33) if p.get('roof_surface')!='metal' else []:
   pts=[r0+ridge_axis*x+cross_axis*(.16*math.cos(a))+np.array([0,0,.16*math.sin(a)+.015]) for a in np.linspace(0,math.pi,11)];verts=pts+[v+ridge_axis*.36 for v in pts];B.mesh('Overlapping curved ridge cap',verts,[(i,i+1,i+12,i+11) for i in range(10)],variants[2])
  if p.get('roof_surface')=='metal':B.line('Metal roof ridge cap',[r0-ridge_axis*.28,r1+ridge_axis*.28],.09,roofmat)
  for end in [0,length]:
   base0=origin+ridge_axis*end;base1=base0+cross_axis*depth;top=base0+cross_axis*depth/2+[0,0,rise];B.mesh('Rectangular-house triangular gable wall',[base0,base1,top],[(0,1,2)],wallmats[1 if along_x else 0])
 elif b['type']=='hip':
  col=np.array(p['roof_color']);tile=material(b['id']+' / blue glazed hip tiles',col,.5);q=np.array([[-.22,-.22,H+.10],[W+.22,-.22,H+.10],[W+.22,D+.22,H+.10],[-.22,D+.22,H+.10]]);rise=min(2.1,min(W,D)*.28)
  if W>=D:r0=np.array([min(D/2,W*.4),D/2,H+rise]);r1=np.array([max(W-D/2,W*.6),D/2,H+rise]);surfaces=[(q[0],q[1],r1,r0),(q[1],q[2],r1,r1),(q[2],q[3],r0,r1),(q[3],q[0],r0,r0)]
  else:r0=np.array([W/2,min(W/2,D*.4),H+rise]);r1=np.array([W/2,max(D-W/2,D*.6),H+rise]);surfaces=[(q[0],q[1],r0,r0),(q[1],q[2],r1,r0),(q[2],q[3],r1,r1),(q[3],q[0],r0,r1)]
  for a,z,r,t in surfaces:
   verts=[a,z,r] if np.allclose(r,t) else [a,z,r,t];B.mesh('True rectangular hipped roof slope',verts,[tuple(range(len(verts)))],tile)
   for f in np.arange(.05,1,.095):B.line('Hip roof glazed tile course',[a+(t-a)*f,z+(r-z)*f],.028,tile)
   for f in np.arange(.01,1,.25/max(1,np.linalg.norm(z-a))):B.line('Glazed tile rib',[a+(z-a)*f,t+(r-t)*f],.035,tile)
   B.line('Hip ridge cap',[a,t],.085,tile)
  B.line('Central glazed roof ridge',[r0,r1],.11,tile)
 if p.get('solar_water_heater'):
  x=W*.5;y=D*.65;z=H+1.2;r=.3;length=1.8;verts=[(x+xx,y+r*math.cos(a),z+r*math.sin(a)) for xx in [-length/2,length/2] for a in np.linspace(0,2*math.pi,24,endpoint=False)];B.mesh('Horizontal solar hot water cylinder',verts,[tuple(range(23,-1,-1)),tuple(range(24,48))]+[(i,(i+1)%24,(i+1)%24+24,i+24) for i in range(24)],STEEL)
  for xx in [x-.73,x+.73]:B.line('Solar water heater support',[(xx,y-.7,H+.1),(xx,y,z),(xx,y+.2,H+.1)],.035,FRAME)
  for xx in np.linspace(x-.75,x+.75,14):B.line('Green solar water collector tube',[(xx,y-.9,H+.2),(xx,y-.12,z-.18)],.041,GLASS)
 for tank in p.get('tanks',[]):
  x=tank['x']*W;y=tank['y']*D;total=tank['height'];rad=tank['radius'];tankh=.9;foot=H+.06;bottom=H+total-tankh;B.cylinder('Source-inferred stainless rooftop water tank',(x,y,bottom+tankh/2),rad,tankh,STEEL,24);B.cylinder('Water tank raised lid',(x,y,bottom+tankh+.035),rad+.025,.065,STEEL,24)
  for zz in [bottom+.12,bottom+tankh-.12]:B.line('Tank circular reinforcing band',[(x+(rad+.012)*math.cos(a),y+(rad+.012)*math.sin(a),zz) for a in np.linspace(0,2*math.pi,33)],.018,STEEL)
  for dx,dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
   B.line('Water tank support leg',[(x+dx*rad*.72,y+dy*rad*.72,bottom),(x+dx*rad*1.05,y+dy*rad*1.05,foot)],.032,STEEL)
   B.box('Tank frame foot pad',(x+dx*rad*1.05,y+dy*rad*1.05,foot),(.17,.17,.06),MORTAR)
  for dy in [-1,1]:
   B.line('Tank frame diagonal cross brace',[(x-rad*.95,y+dy*rad*.95,foot+.15),(x+rad*.75,y+dy*rad*.75,bottom-.10)],.018,STEEL)
   B.line('Tank frame opposite cross brace',[(x+rad*.95,y+dy*rad*.95,foot+.15),(x-rad*.75,y+dy*rad*.75,bottom-.10)],.018,STEEL)
  B.line('Water tank feed pipe',[(x+rad,y,bottom+.22),(x+rad+.18,y,bottom+.22),(x+rad+.18,y,H+.12),(x+rad+.18,.25,H+.12)],.022,trim)
 if p.get('roof_utility_box'):
  u=p['roof_utility_box'];x=u['x']*W;y=u['y']*D;B.box('Source rooftop utility box',(x,y,H+.65),(1.0,.90,1.3),parapet);B.box('Utility box cover',(x,y,H+1.32),(1.16,1.06,.08),trim);B.line('Roof utility vent pipe',[(x,y,H+1.4),(x,y,H+2.4),(x+.28,y,H+2.4)],.065,trim)
 elif b['type'] in ('flat','solar') and not p['tanks']:
  B.cylinder('Roof ventilation upstand',(W*.22,D*.78,H+.25),.13,.50,parapet);B.cylinder('Roof vent cap',(W*.22,D*.78,H+.52),.19,.06,trim)
 return B.finish()
ledger=[r for r in json.loads((OUT/'building_ledger.json').read_text()) if r['id'] not in SELECT] if partial else []
for b in DATA:
 r=make_building(b);ledger.append(r);print('V3_BUILT',r,flush=True)
# Keep source context and the original landmark, while removing unreferenced V1 materials.
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
s.view_layers[0].material_override=None;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=32;s.cycles.use_denoising=True;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.25
s.pop('V2_scope',None)
s['V3_reference_use']='44 and 256 second comparisons, with contextual return frames 252-264 seconds; dimensions remain estimated.'
s.pop('V2_scope',None)
s['V3_scope']='Orthogonal wall plans permit right-angle recesses; 17 return-reviewed units have explicit corrections. Material revision applied across 297 units. Hidden details and metric dimensions remain estimated.'
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:im.pack()
(OUT/'building_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Village_Multiview_Refined.blend'),compress=True);print('V3_CANDIDATE_SAVED',len(ledger),flush=True)
