"""Assemble disjoint building batches with exact inventory coverage."""
import bpy,bmesh,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Matrix
root=Path.cwd();out=root/'outputs/building-quality';s=bpy.context.scene
for c in bpy.data.collections:
 if c.name.startswith(('04 ','06 ','09 ','10 ')):c.hide_render=True;c.hide_viewport=True
parent=bpy.data.collections.new('11 ARCHITECTURE | numbered editable buildings');s.collection.children.link(parent);ledger=[]
material_cache={};image_cache={};data_cache={}
def local_image(image):
 key=(image.filepath_raw,hashlib.sha256(image.packed_file.data).hexdigest() if image.packed_file else image.name)
 if key not in image_cache:
  image_cache[key]=image.copy();assert image_cache[key].library is None
 return image_cache[key]
def local_material(mat):
 key=mat.name if mat.name.startswith('Architecture / ') else mat.as_pointer()
 if key not in material_cache:
  new=mat.copy();assert new.library is None
  if new.use_nodes:
   for node in new.node_tree.nodes:
    if node.bl_idname=='ShaderNodeTexImage' and node.image:node.image=local_image(node.image)
  material_cache[key]=new
 return material_cache[key]
def copy_collection(source,destination):
 col=bpy.data.collections.new(source.name);destination.children.link(col)
 for key in source.keys():col[key]=source[key]
 for ob in source.objects:
  obj=ob.copy();assert obj.library is None
  if ob.data:
   key=ob.data.as_pointer()
   if key not in data_cache:
    data=ob.data.copy();assert data.library is None
    if hasattr(data,'materials'):
     for i,m in enumerate(data.materials):
      if m:data.materials[i]=local_material(m)
    data_cache[key]=data
   obj.data=data_cache[key]
  col.objects.link(obj)
 return col
for folder in ['corrections','batch_0','batch_1','batch_2']:
 path=root/'work/buildings'/folder
 with bpy.data.libraries.load(str(path/'Organized_Architecture.blend'),link=True) as (src,dst):dst.collections=[n for n in src.collections if n.startswith('11 ARCHITECTURE') or (folder=='corrections' and n.startswith('12 CONTEXT'))]
 for col in dst.collections:
  if col.name.startswith('12 CONTEXT'):copy_collection(col,s.collection)
  else:
   for c in col.children:copy_collection(c,parent)
 ledger+=json.loads((path/'building_ledger.json').read_text());print('COPIED_LOCAL_BATCH',folder,len(ledger),flush=True)
bpy.data.orphans_purge(do_local_ids=False,do_linked_ids=True,do_recursive=True);print('UNUSED_LIBRARIES_REMOVED',flush=True)
ids=[c.name.split(' | ')[0] for c in parent.children];expected=[b['id'] for b in json.loads((root/'work/buildings/visibility/architecture_visibility.json').read_text())['buildings']];assert len(ids)==len(set(ids)) and set(ids)==set(expected),(len(ids),len(expected))
for c in parent.children:
 for ob in c.objects:
  if ob.type=='MESH' and any(k in ob.name.lower() for k in ['slab','substrate','hip roof cap']):
   bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
images={}
for im in list(bpy.data.images):
 if im.source!='FILE' or not im.packed_file:continue
 key=(im.filepath_raw,hashlib.sha256(im.packed_file.data).hexdigest())
 if key in images:im.user_remap(images[key]);bpy.data.images.remove(im)
 else:images[key]=im
ca=json.loads((root/'work/buildings/return_camera_roof_candidate.json').read_text());rc=bpy.data.cameras.new('Return 256s | manual roof controls');ro=bpy.data.objects.new(rc.name,rc);s.collection.objects.link(ro);rc.lens=ca['K'][0][0]*36/1600;rc.sensor_width=36;rc.clip_end=3000;M=np.eye(4);M[:3,:3]=np.array(ca['rotation_world_to_camera']).T@np.diag([1,-1,-1]);M[:3,3]=ca['position'];ro.matrix_world=Matrix(M);ro['status']='Manually calibrated reference camera; not registered SfM pose'
s.camera=bpy.data.objects['Video 044.00s | recovered'];s.view_layers[0].material_override=None;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.4;s['Reconstruction_status']=f'{len(ids)} new architectural units; full inventory assembled; visual review pending.'
ledger.sort(key=lambda b:b['id']);(out/'building_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Village_Building_Candidates.blend'),compress=True);print('FULL_ARCHITECTURE_ASSEMBLED',len(ids),flush=True)
