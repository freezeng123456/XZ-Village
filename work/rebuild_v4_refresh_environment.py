import bpy,json,math,os,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.geometry import tessellate_polygon
P=Path('work/rebuild4/architecture').resolve();OUT=P/'village_detailed';d=json.loads((P/'village_mesh_input.json').read_text());sc=bpy.context.scene
src=Path('work/rebuild_v4_build_architecture.py').read_text();exec(src[src.index('def linear'):src.index('ledger=[]')])
for c in list(bpy.data.collections):
 if c.name.startswith('SITE'):
  for ob in list(c.objects):bpy.data.objects.remove(ob,do_unlink=True)
  bpy.data.collections.remove(c)
for ob in list(sc.objects):
 if ob.name=='Terrain':bpy.data.objects.remove(ob,do_unlink=True)
env=json.loads((P/'village_environment.json').read_text());exec(Path('work/rebuild_v4_build_environment.py').read_text());add_environment(env);me=bpy.data.meshes.new('Terrain');me.from_pydata(env['terrain_vertices'],[],env['terrain_faces']);me.materials.append(finish_material('Terrain earth final',[.44,.45,.35],'plaster',.3,2));ob=bpy.data.objects.new('Terrain',me);sc.collection.objects.link(ob)
for face in me.polygons:face.use_smooth=True
sc.camera=bpy.data.objects['source_044'];bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'architecture.blend'))
for sec in [0,44,64,80,90,120,256]:
 dd=next(c for c in d['cameras'] if c['name']==f'source_{sec:03}');sc.camera=bpy.data.objects[dd['name']];sc.render.resolution_x=dd['width'];sc.render.resolution_y=dd['height'];sc.render.filepath=str(OUT/f'detailed_{sec:03}.png');bpy.ops.render.render(write_still=True)
print('ENVIRONMENT REFRESH COMPLETE',flush=True)
