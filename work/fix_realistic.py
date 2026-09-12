import bpy,os,json,math,bmesh
from mathutils import Vector,Matrix
ROOT=os.path.abspath('.');OUT=os.path.join(ROOT,'outputs');AS=os.path.join(ROOT,'work','real_assets');s=bpy.context.scene
cal=json.load(open(os.path.join(AS,'camera.json')));R=Matrix(cal['R']);Rt=R.transposed();campos=Vector(cal['camera']);f=cal['focal']
def unproject(x,y,z):
 d=Rt@Vector(((x*2-1920)/f,(y*2-1080)/f,1));return campos+d*((z-campos.z)/d.z)
def project(v):
 p=R@(v-campos);return((f*p.x/p.z+1920)/3840,1-(f*p.y/p.z+1080)/2160)
def setuv(o):
 uv=o.data.uv_layers.active or o.data.uv_layers.new()
 for l in o.data.loops:uv.data[l.index].uv=project(o.matrix_world@o.data.vertices[l.vertex_index].co)
C=bpy.data.collections['04 Neighbourhood | video-projected context, approximate depth']
ground=bpy.data.objects['Video-ground surface | valid from reference camera'];source=ground.data.materials[0]
bpy.data.objects.remove(ground,do_unlink=True)
verts=[];faces=[];nx=128;ny=90
for j in range(ny+1):
 for i in range(nx+1):verts.append(unproject(i*1920/nx,150+j*930/ny,-.1))
for j in range(ny):
 for i in range(nx):a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
me=bpy.data.meshes.new('Ground with per-pixel perspective interpolation');me.from_pydata(verts,[],faces);me.materials.append(source);ob=bpy.data.objects.new('Video-ground surface | tessellated projection',me);C.objects.link(ob);setuv(ob)
for ob in list(C.objects):
 if ob.type!='MESH' or ob.name.startswith('Video-ground'):continue
 if ob.data.materials and ob.data.materials[0]==source:
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=12,use_grid_fill=True);bm.to_mesh(ob.data);bm.free();setuv(ob)
# The unaltered rectification remains available for comparison; clean photo layer removes duplicated objects.
orig=bpy.data.materials['Target front | rectified source pixels'];clean=orig.copy();clean.name='Target facade | cleaned phototexture'
for n in clean.node_tree.nodes:
 if n.type=='TEX_IMAGE':n.image=bpy.data.images.load(os.path.join(AS,'main_front_clean.png'))
bpy.data.objects['Main facade photo layer'].data.materials[0]=clean
def photoquad(name,verts,material,fn):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[(0,1,2,3)]);me.materials.append(material);o=bpy.data.objects.new(name,me);bpy.data.collections['01 TARGET | surveyed visually from video 45-48 seconds'].objects.link(o);uv=me.uv_layers.new()
 for l in me.loops:uv.data[l.index].uv=fn(me.vertices[l.vertex_index].co)
 return o
windows=[(.85,1.98,8.5,10.22),(.98,2.12,5.16,6.93),(1.12,2.3,1.85,3.55),(3.94,4.77,1.9,2.55)]
for a,b,c,d in windows:photoquad('Window source glazing detail',[(a,.01,c),(b,.01,c),(b,.01,d),(a,.01,d)],orig,lambda v:(v.x/7.5,v.z/10.4))
an=bpy.data.materials['Target annex | rectified source pixels']
for a,b,c,d in [(7.83,9.35,1.2,2.9),(7.62,9.46,4.27,6.55)]:photoquad('Annex original opening detail',[(a,.015,c),(b,.015,c),(b,.015,d),(a,.015,d)],an,lambda v:((v.x-7.5)/2.2,v.z/6.9))
pattern=json.load(open(os.path.join(AS,'tile_pattern.json')));palette={'orange':bpy.data.materials['Terracotta roof tile'],'white':bpy.data.materials['Off-white terrace tile'],'grey':bpy.data.materials['Cool grey terrace tile']}
tiles=sorted([o for o in bpy.data.objects if o.name.startswith('Individual rooftop paving tile')],key=lambda o:(o.location.x,o.location.y))
for ob,color in zip(tiles,pattern):ob.data.materials[0]=palette[color]
# Soften contact shading, matching the hazy overcast drone reference.
s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.2;s.cycles.samples=48
bpy.data.lights['Soft overcast daylight'].energy=1.0
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
s.camera=bpy.data.objects['01 Target detail | original video perspective'];s.render.resolution_x=1400;s.render.resolution_y=1267
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Village_Realistic_Target.blend'))
s.render.filepath=os.path.join(OUT,'Target_Realistic_Closeup.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['02 Village context | source camera'];s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.filepath=os.path.join(OUT,'Village_Reference_View.png');bpy.ops.render.render(write_still=True)
print('FIXED',flush=True)
