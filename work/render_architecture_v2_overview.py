"""Whole-village and neutral geometry views from the saved architectural scene."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
root=Path.cwd();out=root/'outputs/rectangular-photo-refinement';s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.resolution_x=2400;s.render.resolution_y=1600;s.render.resolution_percentage=100
for name,cam in [('Architecture_44s','Video 044.00s | recovered'),('Architecture_Oblique','Review | village oblique'),('Architecture_Return_256s','Return 256s | manual roof controls')]:
 s.render.resolution_x=2000;s.render.resolution_y=1125;s.camera=bpy.data.objects[cam];s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
s.render.resolution_x=2400;s.render.resolution_y=1600
bs=json.loads((root/'work/buildings/v2/inventory.json').read_text())['buildings'];pts=np.vstack([b['roof_world'] for b in bs]);lo=pts.min(0);hi=pts.max(0);center=Vector((lo+hi)/2);center.z=4
camdata=bpy.data.cameras.new('Review | complete village');cam=bpy.data.objects.new(camdata.name,camdata);s.collection.objects.link(cam);camdata.type='ORTHO';camdata.clip_end=5000;cam.location=center+Vector((220,-550,680));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam;bpy.context.view_layer.update();q=np.array([tuple(cam.matrix_world.inverted()@Vector(p)) for p in pts]);camdata.ortho_scale=max(np.ptp(q[:,0])*1.1,np.ptp(q[:,1])*1.5*1.13)
s.render.filepath=str(out/'Whole_Village.png');bpy.ops.render.render(write_still=True)
neutral=bpy.data.materials.new('QA | neutral architectural geometry');neutral.diffuse_color=(.55,.6,.58,1);neutral.use_nodes=True;neutral.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.55,.6,.58,1);neutral.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
s.camera=bpy.data.objects['Review | village oblique'];s.view_layers[0].material_override=neutral;s.render.filepath=str(out/'Geometry_Overview.png');bpy.ops.render.render(write_still=True);s.view_layers[0].material_override=None
# Architectural close views share the same model; no geometry is added for renders.
parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'));original_hide={c:c.hide_render for c in s.collection.children};cs={c.name.split(' | ')[0]:c for c in parent.children}
for name,ids in [('Detail_Modern',['B008','B009','B010']),('Detail_Tile',['O001','O002','O003','O007','O008','O011','O012']),('Detail_Solar',['A004']),('Detail_Construction',['C002'])]:
 selected=[cs[i] for i in ids];points=np.array([tuple(o.matrix_world@Vector(v)) for c in selected for o in c.objects for v in o.bound_box]);mn=points.min(0);mx=points.max(0);cent=Vector((mn+mx)/2);rad=float(np.linalg.norm(mx-mn));cam.location=cent+Vector((.25,-1,.65))*rad*2;cam.rotation_euler=(cent-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=rad*1.07;s.camera=cam
 bpy.context.view_layer.update();cq=np.array([tuple(cam.matrix_world.inverted()@Vector(p)) for p in points]);camdata.ortho_scale=max(np.ptp(cq[:,0])*1.15,np.ptp(cq[:,1])*1.5*1.15)
 for c in parent.children:c.hide_render=c not in selected
 for c in s.collection.children:
  if c!=parent and not c.name.startswith(('05 ','08 ')):c.hide_render=True
 s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 for c in parent.children:c.hide_render=False
 for c,v in original_hide.items():c.hide_render=v
s.camera=bpy.data.objects['Video 044.00s | recovered'];s.render.resolution_x=1600;s.render.resolution_y=900;s.render.filepath=str(out/'Architecture_44s.png');None
print('OVERVIEW_AND_DETAIL_VIEWS_SAVED',flush=True)
