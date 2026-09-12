"""Replace reviewed corrected units while retaining all other building geometry."""
import bpy,json
from pathlib import Path
root=Path.cwd();out=root/'outputs/building-quality';ids=set(json.loads((root/'work/buildings/correction_ids.json').read_text()));parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'))
for c in list(parent.children):
 if c.name.split(' | ')[0] in ids:
  for ob in list(c.objects):bpy.data.objects.remove(ob,do_unlink=True)
  bpy.data.collections.remove(c)
with bpy.data.libraries.load(str(root/'work/buildings/corrections/Village_Building_Candidates.blend'),link=False) as (src,dst):dst.collections=[n for n in src.collections if n.split(' | ')[0] in ids]
for c in dst.collections:parent.children.link(c)
ledger=[b for b in json.loads((out/'building_ledger.json').read_text()) if b['id'] not in ids]+json.loads((root/'work/buildings/corrections/building_ledger.json').read_text());ledger.sort(key=lambda b:b['id']);(out/'building_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2))
# Preserve metadata of the actual merged geometry for review and later rebuilds.
data=json.loads((root/'work/buildings/visibility/architecture_visibility.json').read_text());cols={c.name.split(' | ')[0]:c for c in parent.children}
for b in data['buildings']:
 c=cols[b['id']];slab=next(o for o in c.objects if 'Ground floor closed slab' in o.name);n=len(slab.data.vertices)//2;b['roof_world']=[[v.co.x,v.co.y,float(c['roof_height'])] for v in list(slab.data.vertices)[:n]];b['roof_height']=float(c['roof_height']);b['base_height']=float(c['estimated_ground_height'])
(root/'work/buildings/scene_inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
s=bpy.context.scene;s['Reconstruction_status']='299 new architectural units; merged roof-type and distant-depth corrections; visual review pending';s.camera=bpy.data.objects['Video 044.00s | recovered']
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:im.pack()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Village_Building_Candidates.blend'),compress=True);print('CORRECTED_SCENE_SAVED',len(ledger),flush=True)
