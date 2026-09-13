import bpy,json
from pathlib import Path
from mathutils import Matrix,Vector
root=Path('work/rebuild4/pilot_depth_trial').resolve();d=json.loads((root/'render_camera.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.wm.ply_import(filepath=str(root/'trial_mesh.ply'),forward_axis='Y',up_axis='Z')
obj=bpy.context.object;obj.name='OBSERVED_SURFACE_TRIAL_NOT_FINAL_ARCHITECTURE'
mat=bpy.data.materials.new('Neutral geometry inspection');mat.diffuse_color=(.63,.66,.7,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.63,.66,.7,1);bs.inputs['Roughness'].default_value=.82
obj.data.materials.clear();obj.data.materials.append(mat)
R=Matrix(d['R']);C=Vector(d['center']);rot=R.transposed()@Matrix.Diagonal((1,-1,-1))
bpy.ops.object.camera_add();cam=bpy.context.object;cam.matrix_world=rot.to_4x4();cam.location=C
c=cam.data;fx,fy,cx,cy=d['params'];w,h=d['width'],d['height'];c.sensor_fit='HORIZONTAL';c.sensor_width=36;c.lens=fx/w*36;c.shift_x=(w/2-cx)/w;c.shift_y=(cy-h/2)/w;c.clip_start=.001;c.clip_end=10000
sc=bpy.context.scene;sc.camera=cam
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True
sc.render.resolution_x=1600;sc.render.resolution_y=round(1600*h/w);sc.render.resolution_percentage=100
sc.world.color=(.28,.28,.28)
for i,(direction,energy) in enumerate([((-.4,.5,-1),3),((.7,-.3,-1),1.5)]):
    bpy.ops.object.light_add(type='SUN');li=bpy.context.object;li.data.energy=energy;li.rotation_euler=(rot@Vector(direction)).to_track_quat('-Z','Y').to_euler();li.data.angle=.25
sc.view_settings.view_transform='AgX';sc.render.image_settings.file_format='PNG';sc.render.filepath=str(root/'clay_044.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'trial_surface.blend'))
print('TRIAL_RENDER_COMPLETE',flush=True)
