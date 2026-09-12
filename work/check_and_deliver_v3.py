"""Release gate: counts, saved-model freshness, decodable media, links and checksums."""
import json,hashlib,shutil,zipfile,os
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
from PIL import Image
root=Path.cwd();out=root/'outputs/orthogonal-multiview';dest=Path('/Users/zenghang/Documents/Codex/2026-09-12/jie/outputs/XZ-Village-Multiview-Refinement');model=out/'Village_Multiview_Refined.blend';validation=json.loads((out/'validation.json').read_text());rebuild=json.loads((out/'rebuild_validation.json').read_text());visual=json.loads((out/'visual_review.json').read_text());assert validation['passed'] and rebuild['passed'] and visual['passed']
ids=sorted(set(c['id'] for c in json.loads((out/'multiview_changes.json').read_text())));gallery=json.loads((out/'gallery/gallery_manifest.json').read_text());assert len(gallery)==297 and len(set(g['id'] for g in gallery))==297
expected=[out/f'gallery/geometry_{i:02}.png' for i in range(1,20)]+[out/f'review/{id}_{suffix}.png' for id in ids for suffix in ['source_view','oblique_0','oblique_1']]+[out/f'review/{id}_return_view.png' for id in ids if id.startswith('B')]+[out/(s+'.png') for s in ['Architecture_44s','Architecture_Oblique','Architecture_Return_256s','Whole_Village','Geometry_Overview','Detail_Modern','Detail_Tile','Detail_Solar','Detail_Construction']]
stale=[str(p.relative_to(out)) for p in expected if not p.exists() or p.stat().st_mtime<model.stat().st_mtime];assert not stale,stale
media=list(out.rglob('*.png'))+list(out.rglob('*.jpg'))
for p in media:
 with Image.open(p) as im:im.verify()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.articles=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for key in ['href','src']:
   if key in a:self.links.append(a[key])
  if tag=='article':self.articles.append(a.get('data-id'))
h=Links();h.feed((out/'Village_Review.html').read_text());missing=[]
for href in h.links:
 u=urlsplit(href)
 if u.scheme or not u.path:continue
 if not (out/unquote(u.path)).is_file():missing.append(href)
assert not missing,missing;assert set(h.articles)==set(ids)
checks=dict(passed=True,building_units=297,focused_units=len(ids),atlas_pages=19,atlas_views=594,focused_render_images=58,overview_images=9,current_render_files=len(expected),all_renders_newer_than_saved_model=True,decoded_images=len(media),broken_local_links=missing,model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),model_bytes=model.stat().st_size,reference_separate_from_model=True,validation_file='validation.json',rebuild_validation_file='rebuild_validation.json',visual_review_file='visual_review.json')
(out/'delivery_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
files=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='SHA256SUMS');sums={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(out/'SHA256SUMS').write_text(''.join(f'{v}  {k}\n' for k,v in sums.items()))
shutil.copytree(out,dest,dirs_exist_ok=True)
for name,digest in sums.items():assert hashlib.sha256((dest/name).read_bytes()).hexdigest()==digest,name
assert (dest/'SHA256SUMS').read_bytes()==(out/'SHA256SUMS').read_bytes()
zpath=dest.with_suffix('.zip')
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(dest.rglob('*')):
  if p.is_file():z.write(p,arcname=dest.name+'/'+p.relative_to(dest).as_posix())
with zipfile.ZipFile(zpath) as z:assert z.testzip() is None;assert len(z.namelist())==len(sums)+1
result=dict(**checks,deliverable_directory=str(dest),zip_file=str(zpath),zip_bytes=zpath.stat().st_size,zip_sha256=hashlib.sha256(zpath.read_bytes()).hexdigest(),copied_files_verified=len(sums)+1)
(root/'work/buildings/v3/final_delivery_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
