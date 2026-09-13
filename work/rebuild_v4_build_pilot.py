"""Build the first actual V4 neutral architectural block, without image materials."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.geometry import tessellate_polygon
ROOT=Path('work/rebuild4/architecture').resolve();d=json.loads((ROOT/'pilot_mesh_input.json').read_text());bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
mat=bpy.data.materials.new('Neutral architectural clay');mat.diffuse_color=(.58,.61,.64,1);mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.58,.61,.64,1);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.84
gmat=mat.copy();gmat.name='Neutral terrain clay';gmat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.32,.34,.35,1)
def mesh(name,verts,faces,col,material=mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();me.materials.append(material);ob=bpy.data.objects.new(name,me);col.objects.link(ob);return ob
def prism(name,xy,z0,z1,col):
 n=len(xy);v=[(x,y,z) for z in [z0,z1] for x,y in xy];p=[Vector((x,y,0)) for x,y in xy];faces=[]
 for tri in tessellate_polygon([p]):
  ids=[q if isinstance(q,int) else min(range(n),key=lambda i:(p[i]-q).length) for q in tri];faces.extend([tuple(reversed(ids)),tuple(i+n for i in ids)])
 faces.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]);return mesh(name,v,faces,col)
def beam(name,a,b,width,height,col):
 a=Vector(a);b=Vector(b);u=(b-a).normalized();v=Vector((-u.y,u.x,0));z=Vector((0,0,1));vs=[tuple(p+v*sy*width/2+z*sz*height/2) for p in [a,b] for sy,sz in [(-1,-1),(-1,1),(1,1),(1,-1)]];faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];return mesh(name,vs,faces,col)
for b in d['entries']:
 col=bpy.data.collections.new(b['id']+' | '+b['name']);sc.collection.children.link(col);col['evidence_status']='V4 neutral geometry pilot; not final accepted architecture';col['source_id']=b['id'];col['source_roof_error_px']=b['fit']['rms_px'];xy=b['footprint_world'];z=b['roof_edge_height'];base=b['base_height'];walltop=z if b['roof_type'] in ['hip','metal'] else z-.36;prism(b['id']+' / orthogonal main walls',xy,base,walltop,col)
 if b['roof_type']=='hip':
  m=b['roof_mesh'];mesh(b['id']+' / intersecting hipped roof planes',m['vertices'],m['faces'],col)
 else:prism(b['id']+' / roof structural slab',xy,walltop-.12,walltop+.06,col)
 for j,(a,bb) in enumerate(zip(xy,xy[1:]+xy[:1])):
  if b['roof_type'] not in ['hip','metal']:
   beam(b['id']+f' / parapet {j}',[*a,z-.18],[*bb,z-.18],.17,.36,col);beam(b['id']+f' / parapet coping {j}',[*a,z+.018],[*bb,z+.018],.23,.07,col)
  beam(b['id']+f' / roof cornice {j}',[*a,walltop-.1],[*bb,walltop-.1],.28,.18,col)
  for f in range(1,b['floor_count']):
   level=base+(walltop-base)*f/b['floor_count'];beam(b['id']+f' / floor edge {j}-{f}',[*a,level],[*bb,level],.09,.13,col)
col=bpy.data.collections.new('V4 neutral ground');sc.collection.children.link(col);g=d['ground_mesh'];mesh('Pilot ground from broad-scale source terrain',g['vertices'],g['faces'],col,gmat)
for dd in d['cameras']:
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.name=dd['name'];R=Matrix(dd['R']);rot=R.transposed()@Matrix.Diagonal((1,-1,-1));cam.matrix_world=rot.to_4x4();cam.location=dd['center'];fx,fy,cx,cy=dd['params'];w,h=dd['width'],dd['height'];c=cam.data;c.sensor_fit='HORIZONTAL';c.sensor_width=36;c.lens=fx/w*36;c.shift_x=(w/2-cx)/w;c.shift_y=(cy-h/2)/w;c.clip_start=.05;c.clip_end=10000
sc.world.color=(.4,.4,.4)
for dir,energy in [((-.6,-.7,-1),2.7),((.5,.2,-1),.8)]:
 bpy.ops.object.light_add(type='SUN');light=bpy.context.object;light.data.energy=energy;light.rotation_euler=Vector(dir).to_track_quat('-Z','Y').to_euler();light.data.angle=.18
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=True;sc.view_settings.view_transform='AgX';sc.render.resolution_percentage=100
for sec in [44,256]:
 dd=next(c for c in d['cameras'] if c['name']==f'source_{sec:03}');sc.camera=bpy.data.objects[dd['name']];sc.render.resolution_x=dd['width'];sc.render.resolution_y=dd['height'];sc.render.filepath=str(ROOT/f'pilot_neutral_{sec:03}.png');bpy.ops.render.render(write_still=True)
sc.camera=bpy.data.objects['source_044'];sc['status']='V4 pilot geometry review, no file image textures';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'pilot_neutral.blend'));print('PILOT_GEOMETRY_CREATED',flush=True)
