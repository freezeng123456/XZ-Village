import bpy,json,math,os,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.geometry import tessellate_polygon
P=Path('work/rebuild4/architecture').resolve();OUT=P/'village_detailed';d=json.loads((P/'village_mesh_input.json').read_text());ps={p['id']:p for p in json.loads((P/'village_profiles.json').read_text())['entries']};sc=bpy.context.scene
src=Path('work/rebuild_v4_build_architecture.py').read_text();exec(src[src.index('def linear'):src.index('ledger=[]')]);ids={x['id'] for x in json.loads((P/'final_roof_source_adjudication.json').read_text())['entries']};ledger=json.loads((OUT/'build_ledger.json').read_text());old={e['id']:e for e in ledger['entries']}
for c in list(bpy.data.collections):
 if c.name.split(' | ')[0] in ids:
  for ob in list(c.objects):bpy.data.objects.remove(ob,do_unlink=True)
  bpy.data.collections.remove(c)
for b in d['entries']:
 if b['id'] in ids:old[b['id']]=building(b,ps[b['id']]);print('REFRESH',b['id'],flush=True)
ledger['entries']=[old[b['id']] for b in d['entries']];(OUT/'build_ledger.json').write_text(json.dumps(ledger,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'architecture.blend'))
for sec in [0,44,64,80,90,120,256]:
 dd=next(c for c in d['cameras'] if c['name']==f'source_{sec:03}');sc.camera=bpy.data.objects[dd['name']];sc.render.resolution_x=dd['width'];sc.render.resolution_y=dd['height'];sc.render.filepath=str(OUT/f'detailed_{sec:03}.png');bpy.ops.render.render(write_still=True)
print('ROOF REFRESH COMPLETE',flush=True)
