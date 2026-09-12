import bpy, math, random, os
from mathutils import Vector
random.seed(216)
OUT=os.path.abspath('outputs'); os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
 if c.name!='Collection': bpy.data.collections.remove(c)
base=bpy.data.collections.get('Collection'); base.name='00 Environment'
COL=base
def collection(name):
 global COL
 COL=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(COL)
def link(obj):
 for c in list(obj.users_collection): c.objects.unlink(obj)
 COL.objects.link(obj); return obj
def mat(name,color,noise=0,rough=.8):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 n=m.node_tree.nodes; p=n.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough
 if noise:
  tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=noise; tex.inputs['Detail'].default_value=3
  ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.15; ramp.color_ramp.elements[0].color=(*(v*.55 for v in color),1); ramp.color_ramp.elements[1].position=.85; ramp.color_ramp.elements[1].color=(*(min(1,v*1.2) for v in color),1)
  m.node_tree.links.new(tex.outputs['Fac'],ramp.inputs[0]); m.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color'])
  bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.22; bump.inputs['Distance'].default_value=.13; m.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height']); m.node_tree.links.new(bump.outputs[0],p.inputs['Normal'])
 return m
walls=[mat('Plaster / '+str(i),c,5) for i,c in enumerate([(.69,.69,.63),(.82,.81,.74),(.62,.66,.65),(.72,.75,.73),(.59,.55,.47),(.37,.29,.27),(.76,.68,.57)])]
roof=mat('Weathered concrete',(.39,.4,.37),18); trim=mat('Pale coping and window frames',(.8,.8,.73),9)
glass=mat('Dark blue grey glazing',(.075,.12,.13),0,.28); red=mat('Oxide red railings',(.4,.055,.035),3)
tiles=[mat('Clay roof tiles '+str(i),c,35) for i,c in enumerate([(.38,.16,.085),(.49,.23,.12),(.31,.20,.15),(.47,.29,.2)])]
blue=mat('Blue corrugated metal',(.08,.26,.37),12); solar=mat('Photovoltaic blue',(.026,.059,.09),0,.3)
roadmat=mat('Worn pale concrete road',(.48,.49,.46),30); asphalt=mat('Village asphalt',(.19,.21,.2),30)
soil=mat('Earth',(.26,.235,.15),14); bank=mat('Stone pond embankment',(.30,.32,.27),45)
water=mat('Olive pond water',(.115,.15,.105),2,.2)
fields=[mat('Field '+str(i),c,25) for i,c in enumerate([(.31,.32,.15),(.36,.29,.17),(.45,.40,.27),(.21,.29,.09),(.33,.38,.15),(.42,.39,.30)])]
greens=[mat('Foliage '+str(i),c,4) for i,c in enumerate([(.11,.2,.065),(.18,.27,.08),(.22,.29,.09),(.10,.17,.08),(.25,.32,.1)])]
wood=mat('Tree bark',(.16,.12,.08),10); white=mat('White vehicles',(.85,.86,.83),0,.3)
def mesh(name,verts,faces,m):
 me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update(); ob=bpy.data.objects.new(name,me); COL.objects.link(ob)
 if m: me.materials.append(m)
 return ob
def box(name,loc,scale,m):
 x,y,z=loc; a,b,c=[s/2 for s in scale]
 return mesh(name,[(x+i*a,y+j*b,z+k*c) for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],m)
def line(name,pts,r,m):
 cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=1; cu.bevel_depth=r; cu.bevel_resolution=0
 s=cu.splines.new('POLY'); s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts): p.co=(*v,1)
 ob=bpy.data.objects.new(name,cu); COL.objects.link(ob); ob.data.materials.append(m); return ob
def poly(name,pts,z,m): return mesh(name,[(x,y,z) for x,y in pts],[tuple(range(len(pts)))],m)
def path(name,pts,width,z,m):
 vs=[]
 for i,p in enumerate(pts):
  a=Vector(pts[max(0,i-1)]); b=Vector(pts[min(len(pts)-1,i+1)]); d=(b-a).normalized(); nx=-d.y*width/2; ny=d.x*width/2
  vs.extend([(p[0]+nx,p[1]+ny,z),(p[0]-nx,p[1]-ny,z)])
 return mesh(name,vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)],m)
def rail(pts):
 for z in [.65,1.2]: line('Continuous red handrail',[(x,y,z) for x,y in pts],.07,red)
 for a,b in zip(pts[:-1],pts[1:]):
  n=max(1,int(math.dist(a,b)/1.6))
  for i in range(n+1):
   t=i/n; x=a[0]+(b[0]-a[0])*t; y=a[1]+(b[1]-a[1])*t
   box('Red baluster',(x,y,.68),(.11,.11,1.3),red)
tree_meshes=[]
def tree(x,y,z=0,s=1):
 if not tree_meshes:
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
  template=bpy.context.object
  for m in greens:
   me=template.data.copy(); me.materials.clear(); me.materials.append(m); tree_meshes.append(me)
  bpy.data.objects.remove(template,do_unlink=True)
 line('Tree trunk',[(x,y,z),(x,y,z+3*s)],.18*s,wood)
 for k in range(3):
  ob=bpy.data.objects.new('Tree crown',random.choice(tree_meshes)); COL.objects.link(ob); ob.location=(x+random.uniform(-1,1)*s,y+random.uniform(-1,1)*s,z+(3+k*.6)*s); ob.scale=(2*s,1.7*s,1.7*s)
def house(x,y,w,d,floors,old=False,idx=0):
 h=floors*3.05; wall=random.choice(walls[:5] if old else walls)
 box(f'House {idx:03} | walls',(x,y,h/2+.1),(w,d,h),wall)
 box('Foundation',(x,y,.18),(w+.25,d+.25,.36),bank)
 if old:
  e=h+.1; ridge=e+min(w,d)*.26; m=random.choice(tiles)
  mesh('Pitched clay roof',[(x-w/2-.4,y-d/2-.35,e),(x+w/2+.4,y-d/2-.35,e),(x+w/2+.4,y,ridge),(x-w/2-.4,y,ridge),(x-w/2-.4,y+d/2+.35,e),(x+w/2+.4,y+d/2+.35,e)],[(0,1,2,3),(3,2,5,4)],m)
  for j in range(int(w/.33)+1):
   xx=x-w/2+j*.33
   line('Individual tile course',[(xx,y-d/2-.35,e+.03),(xx,y,ridge+.03),(xx,y+d/2+.35,e+.03)],.055,m)
  line('Roof ridge',[(x-w/2-.45,y,ridge+.07),(x+w/2+.45,y,ridge+.07)],.12,m)
 else:
  box('Roof terrace',(x,y,h+.13),(w+.25,d+.25,.22),roof)
  for yy in [y-d/2,y+d/2]: box('Roof parapet',(x,yy,h+.48),(w+.2,.18,.75),trim)
  for xx in [x-w/2,x+w/2]: box('Roof parapet',(xx,y,h+.48),(.18,d,.75),trim)
  if random.random()<.6:
   box('Roof stair room',(x+w*.24,y+d*.23,h+1.15),(w*.37,d*.37,2),wall)
   box('Stair room cap',(x+w*.24,y+d*.23,h+2.2),(w*.4,d*.4,.15),trim)
  if random.random()<.43:
   for u in range(3):
    for v in range(2):
     p=box('Solar panel',(x-w*.36+u*1.65,y-d*.24+v*2.1,h+.8+v*.18),(1.55,2,.09),solar); p.rotation_euler.x=.085
  if random.random()<.6:
   bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.48,depth=1.1,location=(x+w*.3,y-d*.3,h+1)); ob=link(bpy.context.object); ob.name='Rooftop water tank'; ob.data.materials.append(trim)
 for f in range(floors):
  zz=f*3.05+1.9
  for side in [-1,1]:
   for j in range(max(2,int(w/2.8))):
    xx=x-w/2+(j+.5)*w/max(2,int(w/2.8)); yy=y+side*(d/2+.025)
    box('Window frame',(xx,yy,zz),(1.16,.10,1.42),trim); box('Window glass',(xx,yy+side*.061,zz),(.98,.035,1.22),glass); box('Window mullion',(xx,yy+side*.09,zz),(.055,.04,1.24),trim)
   for j in range(max(1,int(d/3.5))):
    yy=y-d/2+(j+.5)*d/max(1,int(d/3.5)); xx=x+side*(w/2+.03)
    box('Side window frame',(xx,yy,zz),(.1,1.06,1.4),trim); box('Side window',(xx+side*.06,yy,zz),(.03,.87,1.2),glass)
  if not old: box('Floor cornice',(x,y-d/2-.06,f*3.05+.4),(w+.15,.2,.16),trim)
 box('Entrance',(x,y-d/2-.09,1.13),(1.3,.12,2.2),glass)
 if random.random()<.3: box('Entrance metal canopy',(x,y-d/2-.9,2.6),(w*.65,1.8,.1),blue)

box('Landscape base',(0,50,-1.25),(720,850,2),soil)
collection('01 Pond, bridge and red railings')
pond=[(-57,-109),(31,-109),(32,-6),(-24,-6),(-28,-39),(-40,-63),(-57,-81)]
poly('Village main pond',pond,.04,water)
for a,b in zip(pond,pond[1:]+pond[:1]):
 path('Stone retaining edge',[a,b],1.1,.11,bank)
rail(pond+[pond[0]])
left=[(-59,-111),(-59,-81),(-43,-61),(-31,-38),(-27,-4)]
path('Pond side village lane',left,5,.18,asphalt)
path('Main concrete road',[(39,-200),(39,-105),(39,-4),(35,45),(41,108),(54,170),(52,270)],7,.22,roadmat)
rail([(34.8,-112),(34.8,-5),(31,46)])
box('Footbridge deck',(3.5,-5,.55),(64,3.6,.55),roadmat)
for x in [-20,0,22]: box('Bridge pier',(x,-5,-.2),(1.2,3.1,1.2),bank)
rail([(-28,-7),(35,-7)]); rail([(-28,-3),(35,-3)])
poly('Small pond beyond bridge',[(-24,-2),(31,-2),(30,35),(-8,35),(-18,17)],.05,water)
poly('Farm water basin',[(45,14),(76,14),(76,47),(44,47)],.045,water)
for x,y in [(-6,-70),(15,-30),(-48,-88)]:
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,.13)); ob=link(bpy.context.object); ob.name='Floating vegetation'; ob.scale=(2.8,1.8,.22); ob.data.materials.append(greens[2])
for x in [-10,17]: line('Pond aerator pole',[(x,-54,0),(x,-54,3)],.05,wood)

collection('02 Village buildings')
idx=0
# Pond-front silhouettes are deliberately placed; deeper blocks use the observed dense mix.
for x,y,w,d,f in [(-68,-98,10,12,3),(-67,-79,11,10,4),(-53,-62,10,10,3),(-43,-43,11,10,4),(-38,-24,10,11,3),(-36,-4,11,10,4),(-27,17,11,11,3),(-22,35,12,10,2),(-10,48,11,12,3),(12,55,12,12,3),(63,5,12,12,3)]:
 idx+=1; house(x,y,w,d,f,False,idx)
for row in range(15):
 y=-158+row*18
 for col in range(9):
  x=-208+col*18
  if x>-70 and y<-65: continue
  if x>-53 and y<18: continue
  if -149<x<-110 and -70<y<-32: continue
  if random.random()<.1: continue
  idx+=1; old=random.random()<.53
  house(x+random.uniform(-1.8,1.8),y+random.uniform(-2,2),random.uniform(10,14),random.uniform(10,14),random.choice([1,1,2]) if old else random.choice([2,3,3,4,4,5]),old,idx)
for i in range(6): house(-20+i*15,119,10,12,random.choice([3,4]),False,idx+i+1)
collection('03 Village lanes and community square')
for x in [-217,-163,-109,-73]: path('Narrow north south street',[(x,-175),(x,111)],3,.08,roadmat)
for y in [-167,-113,-59,-5,49,103]: path('Narrow cross lane',[(-218,y),(-65,y)],3,.085,roadmat)
box('Community forecourt',(-130,-53,.04),(35,39,.1),roadmat)
house(-133,-39,17,11,1,True,999)
box('Community hall red canopy',(-133,-42,5.3),(18,14,.2),red)
path('Lane to bridge',[(-140,-6),(-30,-6)],4,.12,roadmat)
path('Rear village road',[(-210,133),(-110,133),(-20,133),(40,133),(120,137),(220,145)],6,.15,roadmat)

collection('04 Agricultural strips and irrigation')
for row in range(12):
 y=-175+row*24
 for col in range(5):
  x=54+col*33
  if col==0 and 0<y<55: continue
  m=random.choice(fields); box('Rectangular cultivated plot',(x+15,y+10,.025),(30,20,.08),m)
  for k in range(12): box('Parallel planting ridge',(x+1.2+k*2.4,y+10,.10),(.28,19,.12),random.choice([m,soil]))
for yy in [-180,-108,-36,60,110]: path('Farm access track',[(44,yy),(230,yy+3)],1.7,.16,roadmat)
for xx in [86,152,218]: path('Irrigation ditch',[(xx,-185),(xx,115)],1,.03,water)
for row in range(4):
 for col in range(8):
  x=-240+col*62; y=167+row*43; box('Distant cultivated plot',(x,y,-.03),(59,39,.08),random.choice(fields))
path('Winding farm stream',[(90,40),(107,65),(88,83),(124,105),(162,126),(155,165),(196,189),(183,220),(235,245)],7,.025,water)
for xx in [230,274,318]:
 for yy in [-125,-55,15,85,155,225]: box('Distant aquaculture basin',(xx,yy,-.01),(40,65,.05),water)

collection('05 Woodland and hills')
def terrain_z(x,y): return 4+43*math.exp(-((x+110)/150)**2-((y-320)/95)**2)+22*math.exp(-((x-170)/130)**2-((y-360)/95)**2)
vs=[]; fs=[]; nx=48; ny=23
for j in range(ny):
 for i in range(nx):
  x=-360+i*16; y=250+j*13; vs.append((x,y,terrain_z(x,y)-5))
for j in range(ny-1):
 for i in range(nx-1): a=j*nx+i; fs.append((a,a+1,a+1+nx,a+nx))
mesh('Low wooded hills',vs,fs,greens[0])
for i in range(1200):
 x=random.uniform(-350,370); y=random.uniform(257,520); tree(x,y,terrain_z(x,y)-5,random.uniform(1,1.8))
for i in range(75):
 x=random.uniform(-230,25); y=random.choice([random.uniform(137,159),random.uniform(-180,-172)]); tree(x,y,0,random.uniform(.7,1.1))
for x,y in [(60,-12),(76,5),(-60,-77),(-33,40),(52,70),(94,60),(-110,-60),(-166,110)]: tree(x,y,0,1.4)

collection('06 Road furniture and vehicles')
for y in range(-180,170,20):
 x=44; line('Concrete utility pole',[(x,y,0),(x,y,8)],.12,trim)
 line('Lamp arm',[(x,y,6),(x-1.7,y,6.5)],.07,trim); box('Streetlight',(x-1.6,y,6.5),(.6,.3,.12),trim)
 if y<160:
  for off in [0,.4]: line('Overhead wire',[(x+off,y,7.7),(x+off,y+10,7.1),(x+off,y+20,7.7)],.018,glass)
for i in range(22):
 x,y=random.choice([(39,random.uniform(-145,123)),(-65,random.uniform(-115,-80)),(-35,random.uniform(-35,-10)),(-130+random.uniform(-10,10),-63)])
 carmat=random.choice([white,white,white,glass,red]); box('Car body',(x,y,.65),(1.8,4.1,.8),carmat); box('Car cabin',(x,y+.1,1.2),(1.6,2.1,.7),carmat)
 box('Car front windshield',(x,y-.96,1.35),(1.42,.035,.45),glass); box('Car rear windshield',(x,y+1.17,1.3),(1.42,.035,.4),glass)
 for dx in [-.91,.91]:
  for dy in [-1.2,1.2]: box('Car tire',(x+dx,y+dy,.42),(.2,.63,.63),glass)

collection('07 Cameras and lighting')
scene=bpy.context.scene
def camera(name,pos,target,lens=45):
 bpy.ops.object.camera_add(location=pos); ob=link(bpy.context.object); ob.name=name; ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler(); ob.data.lens=lens; ob.data.clip_end=2500; return ob
cam=camera('01 Drone view - pond and village',(230,-340,275),(-42,22,0),43); scene.camera=cam
camera('02 Above village - old roofs',(-175,-285,260),(-85,-15,0),48)
camera('03 Pond bridge detail',(98,-158,95),(-28,-21,4),49)
bpy.ops.object.light_add(type='SUN',location=(0,0,200)); sun=link(bpy.context.object); sun.name='Soft afternoon sunlight'; sun.rotation_euler=(math.radians(26),math.radians(-24),math.radians(-35)); sun.data.energy=2.2; sun.data.angle=math.radians(18)
scene.world.color=(.5,.5,.5); scene.world.use_nodes=True; bg=scene.world.node_tree.nodes.get('Background'); bg.inputs[0].default_value=(.64,.70,.75,1); bg.inputs[1].default_value=.65
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='OPTIX'; prefs.get_devices()
 for dev in prefs.devices: dev.use=dev.type!='CPU'
 if any(d.use for d in prefs.devices): scene.cycles.device='GPU'
except Exception: pass
scene.render.resolution_x=1600; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene['Source']='DJI video 2026-02-16; frames at 63s and 261s used as primary visual references.'
scene['Reconstruction_note']='Visual reconstruction. Approximate scale and occluded buildings; no survey or photogrammetric solution.'
scene['Building_count']=idx
scene.unit_settings.system='METRIC'
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.region_3d.view_perspective='CAMERA'; area.spaces.active.clip_end=2500
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Village_Reconstruction.blend'))
scene.render.filepath=os.path.join(OUT,'Village_Overview.png'); bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['03 Pond bridge detail']; scene.render.filepath=os.path.join(OUT,'Village_Pond_Detail.png'); bpy.ops.render.render(write_still=True)
print('FINISHED',idx,'buildings',len(bpy.data.objects),'objects',flush=True)
