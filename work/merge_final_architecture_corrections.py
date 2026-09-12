"""Replace only the final reviewed footprint/construction corrections."""
import bpy,json,os
from pathlib import Path
root=Path.cwd();out=root/'outputs/building-quality';folder=root/'work/buildings'/os.environ.get('CORRECTION_FOLDER','roof_fix');ids=set(json.loads((root/'work/buildings'/os.environ.get('CORRECTION_IDS','final_correction_ids.json')).read_text()));parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'))
remove=[]
for c in list(parent.children):
 if c.name.split(' | ')[0] in ids:
  remove.extend(c.objects);remove.append(c)
bpy.data.batch_remove(ids=remove)
with bpy.data.libraries.load(str(folder/'Final_Corrections.blend'),link=False) as (src,dst):dst.collections=[n for n in src.collections if n.split(' | ')[0] in ids]
assert len(dst.collections)==len(ids)
for c in dst.collections:parent.children.link(c)
for name in ['component_organization.json','building_ledger.json']:
 old=json.loads((out/name).read_text());new=json.loads((folder/name).read_text());merged=[b for b in old if b['id'] not in ids]+new;assert len(merged)==299;(out/name).write_text(json.dumps(sorted(merged,key=lambda b:b['id']),ensure_ascii=False,indent=2))
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:im.pack()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Village_Building_Candidates.blend'),compress=True);print('FINAL_CORRECTIONS_MERGED',len(ids),flush=True)
