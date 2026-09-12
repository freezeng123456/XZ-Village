"""Publish the locally reviewed saved scene, only after recorded checks pass."""
import bpy,json,numpy as np
from mathutils import Vector
from pathlib import Path
root=Path.cwd();out=root/'outputs/building-quality';v=json.loads((out/'validation.json').read_text());review=json.loads((out/'visual_review.json').read_text());ids={b['id'] for b in v['buildings']}
assert v['passed'], 'Saved-file checks must pass before local release'
assert set(review['reviewed_ids'])==ids and review['passed'], 'Every new building requires recorded visual review'
s=bpy.context.scene
for c in list(bpy.data.collections):
 if c.name.startswith(('04 ','06 ','09 ','10 ')):
  for ob in list(c.objects):bpy.data.objects.remove(ob,do_unlink=True)
  bpy.data.collections.remove(c)
for c in bpy.data.collections:
 if c.name.split(' | ')[0] in ids:c['status']='Reviewed architectural completion; occluded details inferred with user authorization'
s['Reconstruction_status']=f'{len(ids)+1} numbered architectural units including retained landmark; individually reviewed front/back; approximate completion authorized for unobserved details.'
s['Evidence_boundary']='Video-based roof placement and source appearance; hidden facades, small details, ground heights and dimensions are estimates. Not cadastral or survey reconstruction.'
for text in list(bpy.data.texts):
 if text.name.startswith('ARCHITECTURE | acceptance ledger'):bpy.data.texts.remove(text)
text=bpy.data.texts.new('ARCHITECTURE | reviewed building ledger');text.write(json.dumps(v,ensure_ascii=False,indent=2));text=bpy.data.texts.new('ARCHITECTURE | visual review');text.write(json.dumps(review,ensure_ascii=False,indent=2))
# Keep a practical whole-village opening view in the delivered file.
parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'));parent.name='11 ARCHITECTURE | reviewed numbered buildings'
points=np.array([tuple(o.matrix_world@Vector(v)) for c in parent.children for o in c.objects for v in o.bound_box]);center=Vector((points.min(0)+points.max(0))/2)
cd=bpy.data.cameras.new('DELIVERY | Whole village');camera=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(camera);cd.type='ORTHO';cd.clip_end=5000;camera.location=center+Vector((220,-550,680));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();q=np.array([tuple(camera.matrix_world.inverted()@Vector(p)) for p in points]);cd.ortho_scale=max(np.ptp(q[:,0])*1.12,np.ptp(q[:,1])*1.5*1.12);s.camera=camera;s.render.resolution_x=2400;s.render.resolution_y=1600
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.shading.type='SOLID';space.shading.color_type='MATERIAL';space.shading.show_shadows=True;space.shading.show_cavity=True;space.overlay.show_overlays=False;space.clip_end=5000;space.region_3d.view_perspective='CAMERA'
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:im.pack()
v['counts']['packed_images']=sum(bool(i.packed_file) for i in bpy.data.images);v['saved_file']=str(out/'Village_Reconstructed.blend');ledger=bpy.data.texts.get('ARCHITECTURE | reviewed building ledger');ledger.clear();ledger.write(json.dumps(v,ensure_ascii=False,indent=2))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Village_Reconstructed.blend'),compress=True);print('REVIEWED_LOCAL_RELEASE_SAVED',len(ids)+1)
