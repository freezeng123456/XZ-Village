from pathlib import Path
import json,os,subprocess,concurrent.futures,shutil
root=Path.cwd();bs=json.loads((root/'work/buildings/v2/inventory.json').read_text())['buildings'];out=root/'outputs/rectangular-photo-refinement';blender='/Applications/Blender.app/Contents/MacOS/Blender'
all_ids={b['id'] for b in bs}
if os.environ.get('FINAL_REVIEW_IDS'):bs=[b for b in bs if b['id'] in os.environ['FINAL_REVIEW_IDS'].split(',')]
def run(part):
 selected=bs[part::3];target=root/f'work/buildings/v2/source_part{part}';env=os.environ.copy();env.update(REVIEW_OUT=str(target),REVIEW_WIDTH='600',SOURCE_ONLY='1',REVIEW_SAMPLES='16',REVIEW_IDS=','.join(b['id'] for b in selected))
 with (root/f'work/v2_final_source_{part}.log').open('w') as log:subprocess.run([blender,'-b',str(out/'Village_Rectangular_Candidates.blend'),'-t','4','--python','work/render_architecture_v2_review.py'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 return json.loads((target/'source_view_manifest.json').read_text()),target
merged={r['id']:r for r in json.loads((out/'source_review/source_view_manifest.json').read_text()) if r['id'] in all_ids}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for manifest,target in pool.map(run,range(3)):
  for row in manifest:
   dest=out/'source_review'/f"{row['id']}_source_view.png";shutil.copy2(target/dest.name,dest);row['source_render']=str(dest.relative_to(root));merged[row['id']]=row
(out/'source_review/source_view_manifest.json').write_text(json.dumps(sorted(merged.values(),key=lambda m:m['id']),indent=2));print('SOURCE_BATCH_COMPLETE',len(merged))
