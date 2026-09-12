import bpy,math,os,json,random
from mathutils import Vector,Matrix
random.seed(48)
ROOT=os.path.abspath('.'); OUT=os.path.join(ROOT,'outputs'); AS=os.path.join(ROOT,'work','real_assets')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
def coll(name):
 global C
 C=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(C)
coll('01 TARGET | surveyed visually from video 45-48 seconds')
def obj(name,verts,faces,mat=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);C.objects.link(o)
 if mat:me.materials.append(mat)
 return o
def box(name,loc,dim,mat,bevel=0):
 a,b,c=[v/2 for v in dim]
 o=obj(name,[(i*a,j*b,k*c) for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],mat);o.location=loc
 if bevel:
  m=o.modifiers.new('Small real edge radius','BEVEL');m.width=bevel;m.segments=2
  o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 return o
def line(name,pts,r,mat):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2;s=cu.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 o=bpy.data.objects.new(name,cu);C.objects.link(o);cu.materials.append(mat);return o
def cylinder(name,loc,r,depth,mat,rotation=None):
 verts=[];n=24
 for z in [-depth/2,depth/2]:
  for i in range(n):verts.append((r*math.cos(i*2*math.pi/n),r*math.sin(i*2*math.pi/n),z))
 o=obj(name,verts,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat);o.location=loc
 if rotation:o.rotation_euler=rotation
 for p in o.data.polygons:p.use_smooth=True
 return o
def mat(name,c,rough=.7,noise=0,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if noise:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=noise;tex.inputs['Detail'].default_value=3
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(v*.8 for v in c),1);ramp.color_ramp.elements[1].color=(*(min(1,v*1.12) for v in c),1)
  m.node_tree.links.new(tex.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color'])
  b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.2;b.inputs['Distance'].default_value=.022;m.node_tree.links.new(tex.outputs['Fac'],b.inputs['Height']);m.node_tree.links.new(b.outputs[0],p.inputs['Normal'])
 return m
beige=mat('Warm beige facade / fine mineral texture',(.59,.53,.46),.85,18)
trim=mat('Ivory stone cornice',(.72,.70,.64),.68,65)
groove=mat('Recessed panel joints',(.43,.39,.34),.9)
black=mat('Black powder coated aluminium',(.025,.029,.028),.36,0,.65)
glass=mat('Dark grey glazing',(.08,.11,.105),.23,0,.3)
steel=mat('Stainless steel',(.47,.49,.47),.27,0,.8)
concrete=mat('Weathered grey concrete',(.36,.37,.34),.88,26)
tilewhite=mat('Off-white terrace tile',(.70,.70,.64),.55,40)
tilegrey=mat('Cool grey terrace tile',(.41,.44,.44),.62,40)
terracotta=mat('Terracotta roof tile',(.51,.26,.15),.65,50)
blue=mat('Blue plastic',(.025,.13,.34),.5)
green=mat('Green plastic',(.19,.34,.055),.5)
dark=mat('Interior shadow',(.035,.033,.03),.96)

def image_mat(name,path,emission=.0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(path,check_existing=True);tex.interpolation='Linear';m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.88
 if emission:m.node_tree.links.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=emission
 return m
source=image_mat('Video 48s | perspective UV for surrounding buildings',os.path.join(ROOT,'work','target','t48.jpg'),.22)
fronttex=image_mat('Target front | rectified source pixels',os.path.join(AS,'main_front.png'))
annextex=image_mat('Target annex | rectified source pixels',os.path.join(AS,'lower_front.png'))
rooftex=image_mat('Target roof | source pattern',os.path.join(AS,'main_roof.png'))

def uvmesh(o,fn):
 uv=o.data.uv_layers.new(name='Source coordinates')
 for p in o.data.polygons:
  for li in p.loop_indices:
   v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=fn(v)
def facade(name,x0,x1,z0,z1,y,material,holes=[]):
 xs=sorted(set([x0,x1]+[v for h in holes for v in h[:2]]));zs=sorted(set([z0,z1]+[v for h in holes for v in h[2:]]));vs=[];fs=[]
 for a,b in zip(xs[:-1],xs[1:]):
  for c,d in zip(zs[:-1],zs[1:]):
   if any(h[0]<(a+b)/2<h[1] and h[2]<(c+d)/2<h[3] for h in holes):continue
   k=len(vs);vs.extend([(a,y,c),(b,y,c),(b,y,d),(a,y,d)]);fs.append((k,k+1,k+2,k+3))
 o=obj(name,vs,fs,material)
 uvmesh(o,lambda v:((v.x-x0)/(x1-x0),(v.z-z0)/(z1-z0)));return o
windows=[(.85,1.98,8.5,10.22),(.98,2.12,5.16,6.93),(1.12,2.3,1.85,3.55),(3.94,4.77,1.9,2.55)]
facade('Main south wall | measured openings',0,7.5,0,10.4,0,beige,windows)
# Source color variation is retained on a separate optional layer; crisp geometry supplies detail.
facade('Main facade photo layer',0,7.5,.0,10.4,-.003,fronttex,windows)
box('Main north wall',(3.75,9,5.2),(7.5,.22,10.4),beige)
box('Main west wall',(.1,4.5,5.2),(.2,9,10.4),beige)
box('Main east wall',(7.4,4.5,5.2),(.2,9,10.4),beige)
box('Main ground slab',(3.75,4.5,.05),(7.5,9,.16),concrete)
for z in [3.45,6.9,10.4]:box('Main structural floor',(3.75,4.5,z),(7.5,9,.17),concrete)
for a,b,c,d in windows:
 box('Deep window reveal',((a+b)/2,.12,(c+d)/2),(b-a,.28,d-c),dark)
 box('Recessed window glass',((a+b)/2,.055,(c+d)/2),(b-a-.1,.045,d-c-.1),glass)
 for xx in [a,b,(a+b)/2]:box('Narrow metal window stile',(xx,-.035,(c+d)/2),(.035,.08,d-c),black,.006)
 for zz in [c,d]:box('Window horizontal frame',((a+b)/2,-.035,zz),(b-a+.03,.08,.035),black,.006)
 box('Stone window sill',((a+b)/2,-.10,c-.04),(b-a+.12,.28,.075),trim,.01)
 for j in range(6):box('Window security bar',(a+.1+(b-a-.2)*j/5,-.09,(c+d)/2),(.017,.02,d-c),black)
for x in [i*.4 for i in range(1,19)]:line('Vertical cladding joint',[(x,-.009,.15),(x,-.009,10.37)],.0045,groove)
for y in [i*.4 for i in range(1,23)]:line('Side cladding joint',[(7.51,y,.12),(7.51,y,10.37)],.0045,groove)
line('Front rainwater downpipe',[(5.02,-.08,.28),(5.02,-.08,10.65),(5.02,.4,10.7)],.035,trim)
for z in [1,3.4,5.8,8.2,10]:box('Downpipe fixing clip',(5.02,-.08,z),(.13,.12,.035),trim)
# True three-layer cornice and low parapet, not a fourth storey.
for z,w,d,h in [(10.43,7.78,9.2,.16),(10.58,7.88,9.3,.12)]:box('Projecting roof cornice',(3.75,4.5,z),(w,d,h),trim,.025)
for y in [.07,8.95]:box('Roof low parapet',(3.75,y,10.84),(7.6,.16,.47),concrete,.02);box('Roof parapet coping',(3.75,y,11.09),(7.67,.24,.075),trim,.016)
for x in [.02,7.48]:box('Roof side parapet',(x,4.5,10.84),(.16,9,.47),concrete,.02);box('Roof side coping',(x,4.5,11.09),(.24,9.1,.075),trim,.016)
for i in range(15):
 for j in range(18):
  m=terracotta
  if i<5:m=tilewhite if (i+j*3)%7 in [0,1,2] else tilegrey
  if (i==5 and j<14) or (8<=i<=10 and 2<=j<=5):m=tilewhite
  if i==11 and 12<=j<=14:m=tilegrey
  box('Individual rooftop paving tile',(.27+i*.495,.27+j*.493,10.64),(.48,.48,.045),m,.003)
box('Roof outdoor AC unit',(1.1,8.18,11.0),(.95,.45,.64),tilewhite,.04)
cylinder('AC fan grille',(1.1,7.93,11),.22,.04,steel,(math.pi/2,0,0))
for j in range(9):line('AC grille',[(.9+j*.05,7.89,10.8),(.9+j*.05,7.89,11.2)],.007,steel)
cylinder('Horizontal rooftop water heater',(3.6,8.05,11.15),.27,1.18,steel,(0,math.pi/2,0))
for x in [3.18,4.02]:
 for y in [7.8,8.3]:line('Heater support',[(x,y,10.69),(x,y,11.0)],.035,steel)
line('Roof hot water pipe',[(4.2,8.05,11.15),(4.55,8.05,11.15),(4.55,8.05,10.72),(5,8.05,10.72),(5,8.8,10.72)],.027,trim)
line('Roof vent',[(5.0,8.8,10.7),(5.0,8.8,11.5)],.04,trim)

coll('02 TARGET | two-storey annex and terrace')
annexholes=[(7.83,9.35,1.2,2.9),(7.62,9.46,4.27,6.55)]
facade('Annex south wall',7.5,9.7,0,6.9,0,annextex,annexholes)
box('Annex east wall',(9.6,4.5,3.45),(.2,9,6.9),beige)
box('Annex back wall',(8.6,8.94,3.45),(2.2,.15,6.9),beige)
for z in [3.45,6.9]:box('Annex floor',(8.9,4.5,z),(2.8,9.2,.22),trim,.015)
for a,b,c,d in annexholes:
 box('Annex inner shadow',((a+b)/2,.25,(c+d)/2),(b-a,.05,d-c),dark)
 if c<2:
  box('Annex lower glass',((a+b)/2,.1,(c+d)/2),(b-a-.1,.045,d-c-.1),glass)
  for xx in [a,b,(a+b)/2]:box('Annex window frame',(xx,-.03,(c+d)/2),(.045,.06,d-c),black)
 else:
  for i in range(7):
   cloth=box('Laundry visible within upper opening',(a+.15+i*.22,.27,5.73-random.random()*.35),(.28,.05,.65),random.choice([tilewhite,blue,concrete]));cloth.rotation_euler.y=random.uniform(-.3,.3)
box('Upper terrace paving',(8.93,4.5,7.025),(2.74,8.95,.045),tilegrey)
def railing(name,pts,z):
 for zz in [z+.12,z+.9]:line(name+' horizontal',[(x,y,zz) for x,y in pts],.026,black)
 for a,b in zip(pts[:-1],pts[1:]):
  length=math.dist(a,b);n=math.ceil(length/.13)
  for i in range(n+1):
   t=i/n;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
   line(name+' vertical',[(x,y,z+.1),(x,y,z+.9)],.009 if i%7 else .022,black)
railing('Black terrace railing',[(7.58,-.07),(10.28,-.07),(10.28,8.95),(7.58,8.95)],7.06)
box('Side balcony support',(10.3,.57,1.77),(.2,1.4,3.54),beige)
box('Side balcony slab',(10.05,.55,3.52),(.9,1.5,.15),trim,.02)
railing('Small intermediate balcony',[(9.76,-.13),(10.45,-.13),(10.45,1.3)],3.61)
box('Ground entrance door',(9.97,.09,1.5),(.48,.12,2.8),black)
for k in range(9):box('Door panel grille',(9.97,-.005,.2+k*.3),(.44,.03,.025),steel)
box('Terrace wall AC',(9.85,5.8,7.38),(.5,.85,.62),tilewhite,.025)

coll('03 TARGET | yard, sink, bins and site details')
box('Front paved apron',(5,-.95,-.015),(10.5,1.9,.13),concrete)
for i in range(21):
 for j in range(4):box('Yard stone tile',(-.1+i*.5,-1.7+j*.48,.062),(.49,.47,.033),random.choice([tilegrey,tilewhite,tilegrey]),.002)
box('Front boundary wall',(4.9,-1.91,.38),(10.7,.18,.76),beige,.02)
box('Boundary wall stone cap',(4.9,-1.91,.79),(10.8,.23,.08),trim,.01)
box('West boundary wall',(-.38,3.45,.4),(.17,10.8,.8),concrete)
for y,m in [(-.38,blue),(-.95,green)]:
 cylinder('Plastic refuse bin',(.3,y,.47),.22,.78,m);cylinder('Bin lid',(.3,y,.89),.235,.05,m)
for x in [3.77,4.55]:
 for y in [-.28,-.7]:line('Outdoor washstand legs',[(x,y,.08),(x,y,1.01)],.025,steel)
box('Outdoor wash basin',(4.17,-.5,1.05),(.88,.54,.15),steel,.04)
box('Wash basin interior',(4.17,-.51,1.135),(.66,.36,.012),dark,.04)
line('Basin tap',[(4.2,-.1,1.05),(4.2,-.1,1.39),(4.2,-.35,1.39)],.023,steel)
line('Basin waste pipe',[(4.17,-.5,1.03),(4.17,-.5,.26),(4.17,-.13,.26)],.035,trim)
cylinder('Small exterior wall lamp',(3.91,-.1,2.79),.06,.06,trim,(math.pi/2,0,0))
for x in [10.53,10.9]:box('Gate pier',(x,-.72,.63),(.22,.3,1.25),beige,.02)
line('Foreground service cable',[(-8,-2,5.2),(5,-2,4.4),(15,-2,5.6)],.014,black)

coll('04 Neighbourhood | video-projected context, approximate depth')
cal=json.load(open(os.path.join(AS,'camera.json')));R=Matrix(cal['R']);Rt=R.transposed();campos=Vector(cal['camera']);f=cal['focal']
def unproject(px,py,z):
 d=Rt@Vector(((px*2-1920)/f,(py*2-1080)/f,1));return campos+d*((z-campos.z)/d.z)
def project(v):
 p=R@(v-campos);return ((f*p.x/p.z+1920)/3840,1-(f*p.y/p.z+1080)/2160)
def projected(name,verts,faces):
 o=obj(name,verts,faces,source);uvmesh(o,project);return o
def context_building(name,points,z):
 top=[unproject(x,y,z) for x,y in points];bottom=[Vector((p.x,p.y,.03)) for p in top];n=len(top)
 return projected(name,bottom+top,[tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
context_building('West neighbour | bright blue corrugated roof',[(335,938),(657,962),(636,1021),(300,989)],7.9)
context_building('West attached older concrete house',[(532,840),(793,853),(779,985),(468,954)],5.4)
context_building('Northwest weathered courtyard roof',[(618,737),(857,744),(829,854),(554,836)],6.7)
context_building('Exposed brick neighbour',[(321,733),(444,746),(421,819),(299,799)],7.9)
context_building('West pink neighbour',[(34,865),(334,911),(307,1001),(-25,946)],10.3)
context_building('Rear blue hipped villa',[(708,553),(824,563),(806,620),(766,617),(742,639),(638,626)],13.2)
context_building('Rear villa east lower wing',[(833,552),(920,558),(908,598),(822,592)],9.8)
context_building('Rear white rooftop',[(425,574),(535,584),(521,617),(399,609)],11.4)
context_building('Grey house west of blue villa',[(352,655),(468,670),(454,710),(315,694)],9.5)
context_building('Green window pond-front house',[(838,513),(889,521),(875,551),(815,542)],9.8)
context_building('White pond villa with terrace',[(789,438),(892,448),(880,482),(773,469)],13.8)
context_building('White pond villa upper roof',[(786,390),(895,400),(867,420),(752,411)],13.4)
context_building('Three storey pond villa',[(641,406),(748,426),(728,455),(601,436)],11.2)
context_building('Pond villa side',[(607,437),(725,455),(705,481),(592,464)],10.6)
context_building('Cream villa west pond',[(488,387),(586,400),(567,429),(466,413)],10.5)
context_building('Old warm grey block',[(353,413),(436,429),(410,451),(332,438)],9.7)
context_building('Rear village cream block',[(512,343),(589,354),(568,375),(491,361)],9.5)
context_building('Long peach village building',[(284,251),(403,266),(394,285),(277,270)],10.8)
context_building('West flat-roof residence',[(48,570),(186,600),(158,629),(13,601)],11.3)
context_building('Roadside farm shed',[(1181,911),(1345,931),(1334,975),(1178,960)],3.4)
context_building('White farm-side house',[(1125,208),(1208,208),(1203,231),(1123,230)],9.2)
# Ground is real video texture projected onto geometry; buildings above are separate volumes.
corners=[unproject(x,y,-.1) for x,y in [(0,150),(1920,150),(1920,1080),(0,1080)]]
projected('Video-ground surface | valid from reference camera',corners,[(0,1,2,3)])
# Local geometry beneath the house removes residual source perspective around its base.
box('Road immediately beside target',(12.8,4,-.005),(4.5,29,.08),concrete)
roadverts=[(10.6,-9,.045),(15,-9,.045),(15,18,.045),(10.6,18,.045)]
projected('Road surface photo texture',roadverts,[(0,1,2,3)])

coll('05 Lighting and calibrated cameras')
def camera(name,pos,target,lens):
 ca=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,ca);C.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();ca.lens=lens;ca.clip_end=3000;return o
def cal_camera(name,crop):
 ca=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,ca);C.objects.link(o);o.location=campos
 o.rotation_euler=(Rt@Matrix(((1,0,0),(0,-1,0),(0,0,-1)))).to_euler()
 x0,y0,x1,y1=crop;w=x1-x0;h=y1-y0;ca.lens=f*36/w;ca.sensor_width=36;ca.sensor_fit='HORIZONTAL';ca.shift_x=((x0+x1)/2-1920)/w;ca.shift_y=(1080-(y0+y1)/2)/w;ca.clip_end=3000
 return o
hero=cal_camera('01 Target detail | original video perspective',(1460,1400,2300,2160))
wide=cal_camera('02 Village context | source camera',(0,0,3840,2160))
camera('03 Inspect model from road',(26,-25,20),(4,4,5),48)
camera('04 Roof detail',(16,-14,28),(5,4,7),55)
s=bpy.context.scene;s.camera=hero;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=48;s.cycles.use_denoising=True
s.render.resolution_x=1400;s.render.resolution_y=1267;s.render.resolution_percentage=100
s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs[0].default_value=(.72,.77,.82,1);s.world.node_tree.nodes.get('Background').inputs[1].default_value=.7
sun=bpy.data.lights.new('Soft overcast daylight','SUN');sun.energy=1.35;sun.angle=math.radians(30);o=bpy.data.objects.new('Soft overcast daylight',sun);C.objects.link(o);o.rotation_euler=(.2,-.45,-.5)
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.45
s.unit_settings.system='METRIC';s['Accuracy']='Main landmark manually matched to video frames 45-48s. Nominal width 7.5m and height 10.4m are estimates, not measurements. Context uses source projection and approximate depth.'
s['Source_camera_fit_error_px']=cal['error_pixels']
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_end=3000
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Village_Realistic_Target.blend'))
s.render.filepath=os.path.join(OUT,'Target_Realistic_Closeup.png');bpy.ops.render.render(write_still=True)
s.camera=wide;s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.filepath=os.path.join(OUT,'Village_Reference_View.png');bpy.ops.render.render(write_still=True)
# Independent clay view shows which features exist as geometry.
s.camera=bpy.data.objects['03 Inspect model from road'];s.render.resolution_x=1400;s.render.resolution_y=1100
for o in bpy.data.collections['04 Neighbourhood | video-projected context, approximate depth'].objects:o.hide_render=True
clay=mat('Clay inspection',(.5,.52,.54),.7);s.view_layers[0].material_override=clay;s.render.filepath=os.path.join(OUT,'Target_Geometry_Check.png');bpy.ops.render.render(write_still=True)
print('COMPLETE',len(bpy.data.objects),flush=True)
