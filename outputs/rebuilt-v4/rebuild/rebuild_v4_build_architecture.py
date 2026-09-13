"""Editable source-specific architecture from the fresh V4 geometry and profiles.
Only mathematical shaders and mesh/curve geometry enter this scene.
"""
import bpy,json,math,os,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.geometry import tessellate_polygon
P=Path(__file__).resolve().parent.parent/'data';d=json.loads((P/os.getenv('V4_GEOMETRY','architecture_geometry.json')).read_text());profiles={p['id']:p for p in json.loads((P/os.getenv('V4_PROFILES','architecture_profiles.json')).read_text())['entries']};OUT=P/os.getenv('V4_OUTPUT','rebuilt_from_data');OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);sc=bpy.context.scene
for c in list(bpy.data.collections):
 if c.name!='Collection' and c.users==0:bpy.data.collections.remove(c)
def linear(a):
 a=np.array(a,float);return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def material(name,c,rough=.75,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*linear(c),1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*linear(c),1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;return m
TRIM=material('Aged ivory trim',[.77,.78,.73]);CONCRETE=material('Exposed gray concrete',[.47,.49,.46]);DARK=material('Unlit interior',[.025,.033,.028]);FRAME=material('Dark aluminum window frame',[.17,.19,.18],.45,.5);STEEL=material('Stainless steel',[.60,.64,.65],.27,.78);WOOD=material('Weathered timber',[.32,.245,.16]);SOLAR=material('Solar cells',[.09,.16,.22],.28,.5)
def finish_material(name,c,style,age,axis=0):
 m=material(name,c);nt=m.node_tree;N,L=nt.nodes,nt.links;bs=N.get('Principled BSDF');tex=N.new('ShaderNodeTexCoord');sep=N.new('ShaderNodeSeparateXYZ');L.new(tex.outputs['Object'],sep.inputs[0]);coord=N.new('ShaderNodeCombineXYZ');L.new(sep.outputs['X' if axis in [0,2] else 'Y'],coord.inputs[0]);L.new(sep.outputs['Y' if axis==2 else 'Z'],coord.inputs[1]);rgb=linear(c)
 grain=N.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=45;grain.inputs['Detail'].default_value=3;L.new(coord.outputs[0],grain.inputs['Vector']);macro=N.new('ShaderNodeTexNoise');macro.inputs['Scale'].default_value=.42;macro.inputs['Detail'].default_value=4;L.new(coord.outputs[0],macro.inputs['Vector'])
 if style in ['ceramic','brick','pavers']:
  pat=N.new('ShaderNodeTexBrick');pat.inputs['Scale'].default_value=1;pat.inputs['Brick Width'].default_value=.60 if style=='pavers' else (.24 if style=='brick' else .12);pat.inputs['Row Height'].default_value=.60 if style=='pavers' else (.078 if style=='brick' else .22);pat.inputs['Mortar Size'].default_value=.006 if style in ['brick','pavers'] else .0011;pat.offset=.5 if style=='brick' else 0;pat.inputs['Color1'].default_value=(*(rgb*(.83 if style=='pavers' else .93)),1);pat.inputs['Color2'].default_value=(*(rgb*1.03),1);pat.inputs['Mortar'].default_value=(*(rgb*(.80 if style=='brick' else .88)),1);L.new(coord.outputs[0],pat.inputs['Vector']);surface=pat.outputs['Color'];bump=pat.outputs['Fac']
 else:
  pat=N.new('ShaderNodeValToRGB');pat.color_ramp.elements[0].color=(*(rgb*.94),1);pat.color_ramp.elements[1].color=(*(rgb*1.04),1);L.new(grain.outputs['Fac'],pat.inputs[0]);surface=pat.outputs['Color'];bump=grain.outputs['Fac']
 ramp=N.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.35;ramp.color_ramp.elements[0].color=(age*.12,)*3+(1,);ramp.color_ramp.elements[1].position=.72;ramp.color_ramp.elements[1].color=(age*.75,)*3+(1,);L.new(macro.outputs['Fac'],ramp.inputs[0]);mix=N.new('ShaderNodeMixRGB');mix.inputs[2].default_value=(*linear([.36,.39,.33]),1);L.new(ramp.outputs[0],mix.inputs[0]);L.new(surface,mix.inputs[1]);L.new(mix.outputs[0],bs.inputs['Base Color']);bn=N.new('ShaderNodeBump');bn.inputs['Strength'].default_value=.25;bn.inputs['Distance'].default_value=.008 if style=='brick' else .002;L.new(bump,bn.inputs['Height']);L.new(bn.outputs[0],bs.inputs['Normal']);return m
class Geometry:
 def __init__(self,b):
  self.b=b;self.id=b['id'];xy=np.array(b['footprint_world']);edge=xy[1]-xy[0];self.angle=math.atan2(edge[1],edge[0]);self.R=np.array([[math.cos(self.angle),-math.sin(self.angle)],[math.sin(self.angle),math.cos(self.angle)]]);self.origin=xy.mean(0);self.xy=(xy-self.origin)@self.R;self.base=b['base_height'];self.col=bpy.data.collections.new(self.id+' | '+b['name']);sc.collection.children.link(self.col);self.groups={};self.lines={};self.components=0;self.openings=0;self.inferred=0;self.matrix=Matrix.Translation(Vector((*self.origin,self.base)))@Matrix.Rotation(self.angle,4,'Z')
 def mesh(self,name,vs,fs,mat):
  g=self.groups.setdefault(mat.name,dict(mat=mat,vs=[],fs=[],parts=[]));off=len(g['vs']);g['vs'].extend([tuple(v) for v in vs]);g['fs'].extend([tuple(off+i for i in f) for f in fs]);g['parts'].append(dict(name=name,first_face=len(g['fs'])-len(fs),faces=len(fs)));self.components+=1
 def box(self,name,center,size,mat,basis=None):
  vs=np.array([[-1,-1,-1],[-1,-1,1],[-1,1,-1],[-1,1,1],[1,-1,-1],[1,-1,1],[1,1,-1],[1,1,1]])*np.array(size)/2
  if basis is not None:vs=vs@np.array(basis)
  vs=vs+center;fs=[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)]
  if basis is not None and np.linalg.det(basis)<0:fs=[tuple(reversed(f)) for f in fs]
  self.mesh(name,vs,fs,mat)
 def slab(self,name,z,th,mat,poly=None):
  xy=self.xy.copy() if poly is None else np.array(poly);
  if name=='Floor structural slab':
   ed=np.roll(xy,-1,axis=0)-xy;sgn=1 if np.sum(xy[:,0]*np.roll(xy[:,1],-1)-np.roll(xy[:,0],-1)*xy[:,1])>0 else -1;norm=np.column_stack([ed[:,1],-ed[:,0]])/np.linalg.norm(ed,axis=1)[:,None]*sgn;xy-=.045*(norm+np.roll(norm,1,axis=0))
  holes=self.b.get('roof_openings_world',[]) if z>(self.b['roof_edge_height']-self.base-.65) else []
  if holes:
   hh=[(np.array(q)-self.origin)@self.R for q in holes];xs=sorted(set(xy[:,0].tolist()+[float(x) for q in hh for x in q[:,0]]));ys=sorted(set(xy[:,1].tolist()+[float(y) for q in hh for y in q[:,1]]))
   def inside(p,q):
    yes=False
    for a,b in zip(q,np.roll(q,-1,axis=0)):
     if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes
   for x0,x1 in zip(xs,xs[1:]):
    for y0,y1 in zip(ys,ys[1:]):
     pt=[(x0+x1)/2,(y0+y1)/2]
     if inside(pt,xy) and not any(inside(pt,q) for q in hh):self.box('Roof slab surrounding real aperture',(*pt,z),(x1-x0,y1-y0,th),mat)
   return
  pts=[Vector((x,y,0)) for x,y in xy];n=len(xy);fs=[]
  for tri in tessellate_polygon([pts]):
   ids=[int(q) if isinstance(q,int) else min(range(n),key=lambda i:(pts[i]-q).length) for q in tri];fs.extend([tuple(reversed(ids)),tuple(i+n for i in ids)])
  fs.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]);self.mesh(name,[(*q,z+dz) for dz in [-th/2,th/2] for q in xy],fs,mat)
 def line(self,name,pts,r,mat):
  g=self.lines.setdefault((mat.name,r),dict(mat=mat,r=r,items=[]));g['items'].append((name,pts));self.components+=1
 def cylinder(self,name,c,r,h,mat,n=16):
  x,y,z=c;vs=[(x+r*math.cos(a*math.tau/n),y+r*math.sin(a*math.tau/n),z+dz) for dz in [-h/2,h/2] for a in range(n)];fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];self.mesh(name,vs,fs,mat)
 def done(self):
  for j,g in enumerate(self.groups.values()):
   me=bpy.data.meshes.new(self.id+f' geometry {j:02}');me.from_pydata(g['vs'],[],g['fs']);me.update();me.materials.append(g['mat']);o=bpy.data.objects.new(me.name,me);self.col.objects.link(o);o.matrix_world=self.matrix;o['components']=json.dumps(g['parts']);o['editing']='Independent linked geometric parts inside material groups';o['source_id']=self.id
  for j,g in enumerate(self.lines.values()):
   cu=bpy.data.curves.new(self.id+f' fittings {j:02}','CURVE');cu.dimensions='3D';cu.bevel_depth=g['r'];cu.bevel_resolution=1;cu.materials.append(g['mat'])
   for name,pts in g['items']:
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts):p.co=(*v,1)
   ob=bpy.data.objects.new(cu.name,cu);self.col.objects.link(ob);ob.matrix_world=self.matrix;ob['components']=json.dumps([x[0] for x in g['items']])
  self.col['source_id']=self.id;self.col['observed_and_inferred_detail_ledger']=os.getenv('V4_PROFILES','architecture_profiles.json');self.col['opening_count']=self.openings;self.col['inferred_opening_count']=self.inferred;return dict(id=self.id,openings=self.openings,inferred_openings=self.inferred,components=self.components,vertices=sum(len(o.data.vertices) for o in self.col.objects if o.type=='MESH'))
exec((Path(__file__).resolve().parent/'rebuild_v4_roof_details.py').read_text())
exec((Path(__file__).resolve().parent/'rebuild_v4_distinctive_details.py').read_text())
exec((Path(__file__).resolve().parent/'rebuild_v4_special_buildings_geometry.py').read_text())
exec((Path(__file__).resolve().parent/'rebuild_v4_terrace_geometry.py').read_text())
def building(b,p):
 if b.get('special_model') in ['open_stage','six_column_pavilion']:return special_structure(b,p)
 B=Geometry(b);typ=b['roof_type'];roof=b['roof_edge_height']-B.base;H=max(.6,roof-(.36 if typ=='flat' else (1.05 if typ=='solar' else .12)));n=max(1,b['floor_count']);sh=H/n;xy=B.xy;sign=1 if np.sum(xy[:,0]*np.roll(xy[:,1],-1)-np.roll(xy[:,0],-1)*xy[:,1])>0 else -1;rm=finish_material(B.id+' roof finish',p['roof_color'],'pavers' if typ=='flat' and np.mean(p['roof_color'])>.74 else 'plaster',p.get('roof_age',.2),2);glass=material(B.id+' glass',p.get('glazing_color',[.13,.19,.16]),.3,.23)
 if typ=='metal':H=max(.60,float(np.min(roof_plane(B,b)(xy)))-.04);sh=H/n
 if b.get('source_role')=='canopy' and typ!='solar':
  for a,c in zip(xy,np.roll(xy,-1,axis=0)):
   length=np.linalg.norm(c-a)
   for t in np.linspace(0,1,max(2,int(length/5)+1)):
    q=a+(c-a)*t;top=max(.1,float(roof_plane(B,b)(q)));B.box('Canopy support post',(*q,top/2),(.11,.11,top),STEEL)
   B.line('Canopy perimeter beam',[(*a,float(roof_plane(B,b)(a))-.04),(*c,float(roof_plane(B,b)(c))-.04)],.07,STEEL)
  if typ in ['gable','hip_metal']:pitched_roof(B,b,p,H,rm)
  else:sheet_roof(B,b,p,H,rm)
  return B.done()
 for k in range(n+1):B.slab('Floor structural slab',max(.04,k*sh-.075),.15,rm if k==n else CONCRETE)
 for j,(a2,b2) in enumerate(zip(xy,np.roll(xy,-1,axis=0))):
  f=p['faces'].get(str(j),dict(openings=[],balconies=[],equipment=[],color=p['color'],style=p['style']));a=np.r_[a2,0];u=np.r_[b2-a2,0];L=np.linalg.norm(u);u/=L;out=np.array([u[1],-u[0],0])*sign;basis=np.array([u,out,[0,0,1]]);wm=finish_material(B.id+f' wall {j}',f.get('color',p['color']),f.get('style',p['style']),p.get('wall_age',.2),0 if abs(u[0])>.5 else 1)
  def at(x,z,dep=0):return a+u*x+out*(dep-(1.15 if f.get('public_gallery') else 0))+[0,0,z]
  def boxat(name,x,z,w,h,dep,th,mat):B.box(name,at(x,z,dep),(w,th,h),mat,basis)
  if f.get('curved_stair_bay'):
   curved_stair_bay(B,a,u,out,L,H,wm,glass,f['curved_stair_bay']);continue
  openings=[];logs=[]
  terrace=b.get('top_floor_terrace',{});void=terrace.get('outer_face_voids',{}).get(str(j))
  if void:openings.append([void[0]*L,void[1]*L,terrace['floor']*sh,H,'empty',False])
  for log in f.get('balconies',[]):
   for floor in log['floors']:
    if floor>=n:continue
    l=max(.06,log['x0']*L);r=min(L-.06,log['x1']*L);bt=floor*sh+.09;t=(floor+1)*sh-.20
    if r-l>.5:openings.append([l,r,bt,t,'balcony',log.get('inferred',False)]);logs.append((l,r,bt,t,log))
  for op in f['openings']:
   x0,y0,x1,y1=op['box'];l=max(.10,x0*L);r=min(L-.10,x1*L);bt=max(.10,(1-y1)*H);t=min(H-.12,(1-y0)*H)
   if r-l<.20 or t-bt<.18:continue
   if any(l<rr and r>ll and bt<tt and t>bb for ll,rr,bb,tt,_,_ in openings):continue
   openings.append([l,r,bt,t,op['kind'],op['inferred']])
  xs=sorted(set([0,L]+[v for op in openings for v in op[:2]]));zs=sorted(set([0,H]+[v for op in openings for v in op[2:4]]))
  for l,r in zip(xs,xs[1:]):
   for bt,t in zip(zs,zs[1:]):
    if any(ll<(l+r)/2<rr and bb<(bt+t)/2<tt for ll,rr,bb,tt,_,_ in openings):continue
    boxat('Wall panel around true opening',(l+r)/2,(bt+t)/2,r-l,t-bt,-.12,.24,wm)
  for l,r,bt,t,kind,inferred in openings:
   B.openings+=1;B.inferred+=int(inferred);cx=(l+r)/2;cz=(bt+t)/2;ww=r-l;hh=t-bt
   if kind=='balcony' or kind=='empty' or p['style']=='brick':continue
   boxat('Dark interior beyond opening',cx,cz,ww,hh,-.29,.02,DARK)
   if kind=='vent':
    for z in np.arange(bt+.045,t,.07):boxat('Vent metal louver',cx,z,ww,.025,-.02,.12,FRAME)
    continue
   boxat('Recessed glass pane' if kind=='window' else 'Inset door',cx,cz,ww-.06,hh-.06,-.19,.025,glass if kind=='window' else (material('Observed turquoise public door',[.27,.63,.62]) if f.get('public_gallery') else WOOD))
   for x in [l,(l+r)/2,r]:boxat('Vertical window frame',x,cz,.055,hh,-.10,.09,FRAME)
   for z in [bt,t,bt+hh*.73]:boxat('Horizontal window frame',cx,z,ww,.045,-.10,.09,FRAME)
   boxat('Stone sill',cx,bt-.045,ww+.10,.06,.02,.27,TRIM)
   for x in [l-.035,r+.035]:boxat('Window reveal trim',x,cz,.045,hh+.06,.005,.04,TRIM)
   boxat('Window head trim',cx,t+.035,ww+.10,.045,.005,.06,TRIM)
   if kind=='window' and typ not in ['gable','hip_metal']:
    for x in np.arange(l+.12,r-.04,.17):B.line('Window guard vertical',[at(x,bt+.06,.09),at(x,t-.06,.09)],.01,FRAME)
    for z in [bt+hh*.25,bt+hh*.63]:B.line('Window guard crossbar',[at(l+.04,z,.09),at(r-.04,z,.09)],.01,FRAME)
   if f.get('arch_windows') and kind=='window':arch_spandrel(B,at,l,r,bt,t,wm)
  for l,r,bt,t,log in logs:
   dep=log['depth'];cx=(l+r)/2;cz=(bt+t)/2;ww=r-l;hh=t-bt;boxat('Balcony rear wall',cx,cz,ww,hh,-dep,.16,wm);boxat('Balcony floor',cx,bt-.03,ww,.15,-dep/2,dep+.15,rm)
   for x in [l,r]:B.box('Balcony side return',at(x,cz,-dep/2),(.15,dep,hh),wm,basis)
   dw=min(1.35,ww*.42);boxat('Balcony sliding door reveal',cx,cz,dw,hh*.88,-dep+.095,.03,DARK);boxat('Balcony rear glass',cx,cz,dw-.08,hh*.84,-dep+.12,.025,glass)
   for x in [cx-dw/2,cx,cx+dw/2]:boxat('Balcony rear door frame',x,cz,.045,hh*.88,-dep+.15,.05,FRAME)
   for z in [bt+.14,bt+1.04]:boxat('Balcony railing rail',cx,z,ww,.10,.035,.17,TRIM if log['rail']=='stone' else FRAME)
   for x in np.arange(l+.15,r-.08,.24 if log['rail']=='stone' else .15):
    if log['rail']=='stone':
     for z0,z1,rad in [(.20,.36,.052),(.36,.49,.033),(.49,.72,.055),(.72,.91,.033),(.91,1.01,.05)]:B.cylinder('Turned stone baluster',at(x,bt+(z0+z1)/2,.035),rad,z1-z0,TRIM,10)
    else:B.line('Balcony metal baluster',[at(x,bt+.18,.035),at(x,bt+1.04,.035)],.013,FRAME)
   if log.get('arch'):arch_spandrel(B,at,l,r,bt,t,wm)
  facade_modulations(B,f,at,boxat,L,H,n,basis,wm,glass)
  if f.get('concrete_frame'):
   for x in [.13,L-.13]+([L/2] if L>5 else []):boxat('Exposed concrete column',x,H/2,.26,H,.02,.29,CONCRETE)
   for k in range(1,n+1):boxat('Concrete frame beam',L/2,k*sh-.11,L,.24,.01,.28,CONCRETE)
  roof_segments=[(0,L)] if not void else [(0,void[0]*L),(void[1]*L,L)]
  if typ=='flat' and not f.get('roof_balustrade'):
   for l,r in roof_segments:
    if r-l<.01:continue
    boxat('Roof parapet',(l+r)/2,H+.18,r-l,.36,-.035,.18,CONCRETE if p['style']=='brick' else wm);boxat('Parapet coping',(l+r)/2,H+.385,r-l+.03,.07,-.03,.26,TRIM)
  if typ not in ['gable','hip_metal']:
   for l,r in roof_segments:
    if r-l<.01:continue
    for dz,th in [(-.05,.22),(.06,.29)]:boxat('Roof cornice',(l+r)/2,H+dz,r-l+.07,.075,0,th,TRIM)
   boxat('Damp-proof plinth',L/2,.19,L,.38,.015,.07,CONCRETE)
  if typ=='metal':boxat('Folded sheet roof fascia',L/2,H-.20,L,.54,.025,.08,rm)
  if j%2==0 and L>2:
   x=L-.17;B.line('Rainwater downpipe',[at(x,H,.13),at(x,.3,.13),at(x,.16,.32)],.035,TRIM)
   for z in np.arange(.8,H,1.7):boxat('Pipe wall bracket',x,z,.12,.04,.13,.08,FRAME)
  for e in f.get('equipment',[]):
   x=e['x']*L;z=(1-e['y'])*H;boxat('Source air conditioner',x,z,.77,.54,.27,.44,TRIM)
   for xx in np.linspace(x-.27,x+.27,10):B.line('Condenser grille',[at(xx,z-.17,.50),at(xx,z+.17,.50)],.01,FRAME)
   B.line('Condenser drain line',[at(x+.40,z,.25),at(x+.51,z-.12,.15),at(x+.51,z-.92,.15)],.014,TRIM)
 if b.get('top_floor_terrace'):add_top_terrace(B,b,p,H,finish_material(B.id+' terrace wall',p['color'],p['style'],.3,0))
 if typ=='hip' and 'roof_mesh' in b:
  m=b['roof_mesh'];v=np.array(m['vertices']);v[:,:2]=(v[:,:2]-B.origin)@B.R;v[:,2]-=B.base;B.mesh('Source compound hip roof',v,m['faces'],rm)
  for a,z in zip(xy,np.roll(xy,-1,axis=0)):B.line('Roof eave edge',[(*a,roof),(*z,roof)],.07,rm)
 if b.get('special_model') in ['curved_ridge_hall','curved_ridge_gate']:traditional_roof(B,b,p,H,rm)
 elif typ in ['gable','hip_metal'] or (typ=='hip' and 'roof_mesh' not in b):pitched_roof(B,b,p,H,rm)
 if typ in ['metal','solar']:sheet_roof(B,b,p,H,rm)
 # Equipment and roof repairs are individually annotated in the new profile.
 mn=xy.min(0);mx=xy.max(0)
 for e in p.get('equipment',[]):
  c=mn+(mx-mn)*e['xy'];z=H
  if e['type']=='tank':
   radius=e.get('radius',.53);height=e.get('height',1.3);stand=e.get('stand',.65)
   for dx,dy in [(-.65,-.65),(.65,-.65),(-.65,.65),(.65,.65)]:B.box('Tank support leg',(*(c+np.array([dx,dy])*radius),z+stand/2),(.055,.055,max(.05,stand)),STEEL)
   B.cylinder('Roof water tank',(*c,z+stand+height/2),radius,height,STEEL,24)
   for h in [.04,height*.5,height-.04]:B.cylinder('Tank circumferential band',(*c,z+stand+h),radius+.015,.045,STEEL,24)
   B.cylinder('Tank top cap',(*c,z+stand+height+.035),radius*.3,.07,STEEL,16)
  if e['type']=='vent':
   h=e.get('height',1.3);B.cylinder('Roof vent flue',(*c,z+h/2),.11,h,TRIM)
  if e['type']=='roof_ac':
   B.box('Roof condenser housing',(*c,z+.31),(.8,.38,.58),TRIM)
   for x in np.linspace(-.25,.25,11):B.line('Roof condenser grille',[(*(c+[x,-.21]),z+.10),(*(c+[x,-.21]),z+.50)],.008,FRAME)
  if e['type']=='heater':
   vs=[(c[0]+dx,c[1]+.325*math.cos(a*math.tau/24),z+.72+.325*math.sin(a*math.tau/24)) for dx in [-.85,.85] for a in range(24)];fs=[tuple(range(23,-1,-1)),tuple(range(24,48))]+[(a,(a+1)%24,(a+1)%24+24,a+24) for a in range(24)];B.mesh('Horizontal cylindrical water heater',vs,fs,STEEL)
   for x in [-.57,.57]:B.box('Heater support',(*(c+[x,0]),z+.22),(.07,.5,.44),STEEL)
   B.box('Solar water heater collector',(*(c+[0,-.57]),z+.33),(1.65,.95,.055),SOLAR)
   for x in np.arange(-.75,.78,.09):B.line('Solar collector vacuum tube',[(*(c+[x,-.98]),z+.40),(*(c+[x,-.18]),z+.48)],.025,STEEL)
  if e['type']=='pergola':
   w=e.get('width',2.6);dep=e.get('depth',2.2);ht=e.get('height',2.5)
   for dx in [-w/2,w/2]:
    for dy in [-dep/2,dep/2]:B.box('Source terrace pergola column',(*(c+[dx,dy]),z+ht/2),(.11,.11,ht),TRIM)
   for yy in [-dep/2,dep/2]:B.box('Pergola primary beam',(*(c+[0,yy]),z+ht),(w+.30,.13,.14),TRIM)
   for xx in np.linspace(-w/2,w/2,7):B.box('Pergola overhead slat',(*(c+[xx,0]),z+ht+.10),(.12,dep+.45,.12),TRIM)
 if p.get('roof_pattern'):
  rng=np.random.default_rng(sum(map(ord,B.id)));mats=[finish_material(B.id+f' roof paving patch {k}',cc,'pavers',.22,2) for k,cc in enumerate([[.86,.86,.80],[.67,.69,.67],[.90,.89,.83],[.60,.63,.62],[.82,.76,.64]])]
  for x in np.arange(mn[0],mx[0],1.12):
   for y in np.arange(mn[1],mx[1],.80):
    if rng.random()<.64 and all(inside_polygon(q,xy) for q in [[x+.05,y+.05],[x+1.04,y+.05],[x+1.04,y+.72],[x+.05,y+.72]]) and not any(inside_polygon([x+.55,y+.38],(np.array(hole)-B.origin)@B.R) for hole in b.get('roof_openings_world',[])):B.box('Source-type irregular roof repair tile',(x+.55,y+.38,H+.016),(1.09,.77,.025),mats[int(rng.integers(len(mats)))])
 for e in p.get('roof_patches',[]):
  r=e['rect'];aa=mn+(mx-mn)*r[:2];bb=mn+(mx-mn)*r[2:];mat=finish_material(B.id+' roof repair',e['color'],'plaster',.15,2);B.box('Source roof repair area',(*(aa+bb)/2,H+.012),(*(bb-aa),.012),mat)
 return B.done()
ledger=[]
for b in d['entries']:
 if b['id'] not in profiles:continue
 ledger.append(building(b,profiles[b['id']]));print('BUILT',ledger[-1],flush=True)
# Model-only terrain and source cameras. Source JPEG paths are provenance metadata only.
g=d.get('ground_mesh')
if g:
 verts=np.array(g['vertices']);xs=np.unique(verts[:,0]);ys=np.unique(verts[:,1]);grid=verts[:,2].reshape(len(ys),len(xs))
 for _ in range(2):grid[1:-1,1:-1]=grid[1:-1,1:-1]*.5+(grid[:-2,1:-1]+grid[2:,1:-1]+grid[1:-1,:-2]+grid[1:-1,2:])*.125
 verts[:,2]=grid.ravel();envpath=P/'village_environment.json'
 if envpath.exists():
  env=json.loads(envpath.read_text())
  if env.get('terrain_vertices'):verts=np.array(env['terrain_vertices']);g['faces']=env.get('terrain_faces',g['faces'])
  exec((Path(__file__).resolve().parent/'rebuild_v4_build_environment.py').read_text());add_environment(env)
 me=bpy.data.meshes.new('Terrain');me.from_pydata(verts.tolist(),[],g['faces']);me.materials.append(finish_material('Terrain earth',[.44,.45,.35],'plaster',.3,2));ob=bpy.data.objects.new('Terrain',me);sc.collection.objects.link(ob)
 for face in me.polygons:face.use_smooth=True
for dd in d['cameras']:
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.name=dd['name'];cam.matrix_world=(Matrix(dd['R']).transposed()@Matrix.Diagonal((1,-1,-1))).to_4x4();cam.location=dd['center'];fx,fy,cx,cy=dd['params'];w,h=dd['width'],dd['height'];cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=36;cam.data.lens=fx/w*36;cam.data.shift_x=(w/2-cx)/w;cam.data.shift_y=(cy-h/2)/w;cam.data.clip_start=.05;cam.data.clip_end=10000
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.67,.74,.82,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
bpy.ops.object.light_add(type='SUN');light=bpy.context.object;light.data.energy=2.5;light.rotation_euler=Vector((-.55,.30,-1)).to_track_quat('-Z','Y').to_euler();light.data.angle=.18
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=True;sc.view_settings.view_transform='AgX';sc.render.resolution_percentage=int(os.getenv('V4_RENDER_PERCENT','75'))
sc.camera=bpy.data.objects['source_044'];bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'architecture.blend'))
for sec in [int(x) for x in os.getenv('V4_RENDER_VIEWS','44,256').split(',') if x]:
 dd=next(c for c in d['cameras'] if c['name']==f'source_{sec:03}');sc.camera=bpy.data.objects[dd['name']];sc.render.resolution_x=dd['width'];sc.render.resolution_y=dd['height'];sc.render.filepath=str(OUT/f'detailed_{sec:03}.png');bpy.ops.render.render(write_still=True)
sc.camera=bpy.data.objects['source_044'];sc['reconstruction_status']='Source-located V4 editable village reconstruction. Source-supported exterior details and explicit inference coexist; no surveyed scale.';sc['no_photo_materials']=True;sc['scale_status']='Provisional common scale, no surveyed dimensions';bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'architecture.blend'));(OUT/'build_ledger.json').write_text(json.dumps(dict(entries=ledger,file_image_count=sum(i.source=='FILE' for i in bpy.data.images)),indent=2));print('SAVED',flush=True)
