"""Remove all photographic scenery and photo-only facade overlays from the delivered scene."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
root=Path.cwd();out=root/'outputs/rectangular-photo-refinement';s=bpy.context.scene
photo_names=[o.name for o in bpy.data.objects if o.name=='Main facade photo layer' or o.name.startswith(('Window source glazing detail','Annex original opening detail'))]
def landmark_hash():
 obs=sorted([o for c in bpy.data.collections if c.name.startswith(('01 TARGET','02 TARGET','03 TARGET')) for o in c.objects if o.name not in photo_names],key=lambda o:o.name);h=hashlib.sha256()
 for ob in obs:
  h.update(ob.name.encode());h.update(ob.type.encode());h.update(np.array(ob.matrix_world,dtype='<f8').tobytes())
  if ob.type=='MESH':
   v=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',v);h.update(v.tobytes());i=np.empty(len(ob.data.loops),np.int32);ob.data.loops.foreach_get('vertex_index',i);h.update(i.tobytes())
  elif ob.type=='CURVE':
   for sp in ob.data.splines:h.update(np.array([p.co[:] for p in sp.points],dtype='<f4').tobytes())
   h.update(str(ob.data.bevel_depth).encode())
 return len(obs),h.hexdigest()
n,h=landmark_hash();removed=[]
for c in list(bpy.data.collections):
 if c.name.startswith(('04 ','06 ','09 ','10 ','12 ')):
  for o in list(c.objects):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
for name in photo_names:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
# The annex wall is actual modeled geometry; replace its photo material with the existing mineral finish.
wall=bpy.data.objects.get('Annex south wall')
if wall:
 for i,m in enumerate(wall.data.materials):
  if m and m.use_nodes and any(node.type=='TEX_IMAGE' for node in m.node_tree.nodes):wall.data.materials[i]=bpy.data.materials['Warm beige facade / fine mineral texture']
for cam in bpy.data.cameras:
 cam.show_background_images=False
 for bg in list(cam.background_images):cam.background_images.remove(bg)
for ob in list(bpy.data.objects):
 if ob.type=='EMPTY' and ob.empty_display_type=='IMAGE':removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
for m in list(bpy.data.materials):
 if m.use_nodes and any(node.type=='TEX_IMAGE' for node in m.node_tree.nodes):
  assert m.users==0,m.name
  bpy.data.materials.remove(m)
for im in list(bpy.data.images):
 if im.source=='FILE':bpy.data.images.remove(im)
assert landmark_hash()==(n,h)
s['clean_structure']=True;s['clean_landmark_object_count']=n;s['clean_landmark_geometry_sha256']=h
s['Evidence_boundary']='Pure modeled geometry with procedural/solid materials; no photographic ground, source-image texture, facade photo layer or camera background. Source photographs appear only in separate comparison panels.'
# Default opens on the useful nearby village view rather than the very distant full route.
s.camera=bpy.data.objects['Video 044.00s | recovered'];s.render.resolution_x=2000;s.render.resolution_y=1125
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
manifest={'removed_ground_and_backdrop_objects':removed,'removed_photo_only_facade_objects':photo_names,'photo_only_facade_objects_removed':len(photo_names),'remaining_landmark_objects':n,'remaining_landmark_geometry_unchanged':True,'remaining_landmark_geometry_sha256':h,'annex_wall_material':'Warm beige facade / fine mineral texture','source_image_datablocks_remaining':sum(i.source=='FILE' for i in bpy.data.images),'image_texture_nodes_remaining':sum(node.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for node in m.node_tree.nodes),'camera_backgrounds_remaining':sum(len(c.background_images) for c in bpy.data.cameras),'preserved':'297 refined building units; physical geometry of the landmark except seven photographic overlay planes; modeled pond and railings','comparison_policy':'Original source and model render occupy separate labeled panels; source pixels are never laid under or over the model.'}
(out/'clean_structure_audit.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));t=bpy.data.texts.get('ARCHITECTURE | clean structure') or bpy.data.texts.new('ARCHITECTURE | clean structure');t.clear();t.write(json.dumps(manifest,ensure_ascii=False,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Village_Rectangular_Refined.blend'),compress=True);print('CLEAN_STRUCTURE_SAVED',json.dumps(manifest,ensure_ascii=False))
