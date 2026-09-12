import bpy
from pathlib import Path
s=bpy.context.scene
for c in s.collection.children:c.hide_render=not c.name.startswith(('01 ','02 ','03 ','05 ','08 '))
s.camera=bpy.data.objects['01 Target detail | original video perspective'];s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.render.filepath=str(Path.cwd()/'outputs/rectangular-photo-refinement/Landmark_Original.png');bpy.ops.render.render(write_still=True)
