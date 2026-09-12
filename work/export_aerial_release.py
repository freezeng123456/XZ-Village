"""Gather the inspected release, supporting evidence and source comparison."""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from aerial_common import main_model_path
root=Path('work/aerial');out=Path('outputs/aerial-continuation');ev=out/'evidence';ev.mkdir(exist_ok=True)
mapping={
 'reference/source_manifest.json':'source_manifest.json',
 'sfm/frames.json':'sfm_frames.json','sfm/config.json':'sfm_config.json','sfm/summary.json':'sfm_summary.json',
 'sfm/flow/summary.json':'dense_flow_summary.json','sfm/dense/summary.json':'sgbm_diagnostic_summary.json',
 'alignment.json':'alignment.json','package/summary.json':'surface_summary.json',
 'package/site_traces.json':'site_traces.json','package/neighbour_roofs.json':'neighbour_roofs.json',
 'package/cameras.json':'recovered_cameras.json',
 'landmark_before.json':'landmark_before.json','landmark_after.json':'landmark_after.json',
}
for src,dst in mapping.items():
    if (root/src).exists():shutil.copy2(root/src,ev/dst)
before=json.loads((root/'landmark_before.json').read_text());after=json.loads((root/'landmark_after.json').read_text())
assert before==after,'Baseline landmark geometry changed'
(ev/'landmark_preservation.json').write_text(json.dumps(dict(passed=True,**before),indent=2)+'\n')
shutil.copy2(root/'package/Village_Observed_Points.ply',out/'Village_Observed_Points.ply')
shutil.copy2(root/'package/Reference_48s_Undistorted.jpg',out/'Reference_48s_Undistorted.jpg')
shutil.copy2(root/'reference/contact_sheet.jpg',out/'Source_Contact_Sheet.jpg')
shutil.copy2(root/'roof_candidates.jpg',ev/'roof_candidates_review.jpg')
shutil.copytree(main_model_path(root/'sfm'),ev/'main_sparse',dirs_exist_ok=True)
sfm=json.loads((root/'sfm/summary.json').read_text())
for model in sfm['models']:
    if 'f260.00.jpg' in model['image_names']:shutil.copytree(root/'sfm/sparse'/str(model['id']),ev/'return_sparse',dirs_exist_ok=True)
panel=Image.new('RGB',(1920,648),'#eef0eb');draw=ImageDraw.Draw(panel)
try:font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',24)
except OSError:font=ImageFont.load_default(size=24)
for i,(name,label) in enumerate([('Reference_48s_Undistorted.jpg','SOURCE / 48s (undistorted)'),('Village_Structural_48s.png','CONTINUATION / surfaces + structural drafts')]):
    im=Image.open(out/name).convert('RGB')
    panel.paste(im.resize((960,540)),(i*960,54));draw.text((i*960+18,14),label,font=font,fill='#1b292a')
draw.text((18,610),'Partial reconstruction: gaps remain; scale estimated; unseen facades approximate.',font=font,fill='#334447')
panel.save(out/'Reference_Comparison.jpg',quality=94)
checks={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
(out/'SHA256SUMS.json').write_text(json.dumps(checks,indent=2)+'\n')
print('Exported',len(checks),'files')
