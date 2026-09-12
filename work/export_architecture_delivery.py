"""Export only final user-facing deliverables and source snapshots."""
from pathlib import Path
import shutil,json
root=Path.cwd();src=root/'outputs/building-quality';dest=root.parent.parent/'outputs/XZ-Village-Full-Reconstruction';dest.mkdir(parents=True,exist_ok=True)
assert json.loads((src/'validation.json').read_text())['passed']
for p in src.iterdir():
 if p.name in ('Village_Building_Candidates.blend','Village_Building_Candidates.blend1') or p.suffix in ('.blend1','.blend2'):continue
 if p.is_dir():
  if p.name=='review':shutil.copytree(p,dest/p.name,dirs_exist_ok=True)
 elif p.suffix in ('.blend','.png','.jpg','.json','.csv','.html','.md'):shutil.copy2(p,dest/p.name)
source=dest/'source';source.mkdir(exist_ok=True)
names=['build_architecture','condense_architecture_components','assemble_architecture_batches','clean_architecture_materials','finish_roof_seams','merge_final_architecture_corrections','validate_architecture','building_gallery','render_architecture_overview','package_building_review','finalize_architecture','write_architecture_report','export_architecture_delivery','sample_architecture_finishes','review_coverage_projections','aerial_common','prepare_architecture','refine_visible_facades','prepare_architecture_ground','place_observed_roof_fixtures','regularize_distant_roofs','apply_reviewed_roof_corrections']
for name in names:shutil.copy2(root/'work'/f'{name}.py',source/f'{name}.py')
data=source/'specifications';data.mkdir(exist_ok=True)
for p in (root/'work/buildings').glob('*.json'):shutil.copy2(p,data/p.name)
for name in ['architecture_visibility.json','poses.json']:shutil.copy2(root/'work/buildings/visibility'/name,data/name)
shutil.copy2(root/'REPRODUCE_ARCHITECTURE.md',dest/'REPRODUCE_ARCHITECTURE.md')
print('DELIVERY_EXPORTED',dest)
