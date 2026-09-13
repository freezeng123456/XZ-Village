"""Render every inventoried building from two viewpoints for visual review."""
import bpy,json,math,os
import numpy as np
from mathutils import Vector,Matrix
from pathlib import Path
root=Path.cwd();out=root/os.environ.get('GALLERY_OUT','work/rebuild4/architecture/final_gallery');out.mkdir(parents=True,exist_ok=True)
original=bpy.context.scene
bs=json.loads((root/os.environ.get('ARCHITECTURE_SPEC','work/rebuild4/architecture/village_mesh_input.json')).read_text())['entries']
if os.environ.get('GALLERY_IDS'):bs=[b for b in bs if b['id'] in os.environ['GALLERY_IDS'].split(',')]
collections={c.name.split(' | ')[0]:c for c in bpy.data.collections if c.name.split(' | ')[0] in {b['id'] for b in bs}}
scene=bpy.data.scenes.new('Per-building review');scene.world=original.world.copy();scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=2400;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=float(os.environ.get('GALLERY_EXPOSURE','0'));scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.30,.34,.35,1)
for ob in original.objects:
 if ob.type=='LIGHT':scene.collection.objects.link(ob)
camdata=bpy.data.cameras.new('Review atlas camera');cam=bpy.data.objects.new(camdata.name,camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=56
angle=math.radians(28);up=Vector((0,math.sin(angle),math.cos(angle)));right=Vector((1,0,0));view=Vector((0,-math.cos(angle),math.sin(angle)));cam.location=view*100;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
manifest=[]
start=int(os.environ.get('START_PAGE','0'));end=int(os.environ.get('END_PAGE','999'))
for page in range((len(bs)+15)//16):
 if not start<=page<end:continue
 if os.environ.get('GALLERY_PAGES') and page+1 not in {int(x) for x in os.environ['GALLERY_PAGES'].split(',')}:continue
 tmp=bpy.data.collections.new('Review batch');scene.collection.children.link(tmp)
 for index,b in enumerate(bs[page*16:(page+1)*16]):
  col=collections[b['id']];points=np.array([tuple(ob.matrix_world@Vector(corner)) for ob in col.objects for corner in ob.bound_box if ob.type in ('MESH','CURVE')]);lo=points.min(0);hi=points.max(0);center=(lo+hi)/2;radius=np.linalg.norm(hi-lo);scale=5.7/max(radius,1);p=np.array(b['footprint_world']);edge=p[1]-p[0];theta=math.atan2(edge[1],edge[0])
  for side in range(2):
   x=(index%4)*2+side;y=index//4;offset=right*((x-3.5)*7)+up*((1.5-y)*7)
   rotation=Matrix.Rotation(-theta+(-.60 if side==0 else math.pi-.60),4,'Z');transform=Matrix.Translation(offset)@Matrix.Scale(scale,4)@rotation@Matrix.Translation(Vector(-center))
   obj=bpy.data.objects.new(b['id']+' view '+str(side),None);obj.instance_type='COLLECTION';obj.instance_collection=col;tmp.objects.link(obj);obj.matrix_world=transform
  manifest.append(dict(id=b['id'],page=page+1,column=index%4,row=index//4,views=['front_oblique','opposite_oblique']))
 scene.render.filepath=str(out/f'geometry_{page+1:02}.png');bpy.context.window.scene=scene;bpy.ops.render.render(write_still=True);print('REVIEW_PAGE',page+1,flush=True)
 for ob in list(tmp.objects):bpy.data.objects.remove(ob,do_unlink=True)
 bpy.data.collections.remove(tmp)
manifest_path=out/'gallery_manifest.json'
if os.environ.get('GALLERY_PAGES') and manifest_path.exists():
 old=json.loads(manifest_path.read_text());changed={r['id'] for r in manifest};manifest=[r for r in old if r['id'] not in changed]+manifest;manifest.sort(key=lambda r:(r['page'],r['row'],r['column']))
manifest_path.write_text(json.dumps(manifest,indent=2))
