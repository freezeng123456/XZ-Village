"""Seal the validated delivery after browser review."""
from pathlib import Path
import json,hashlib,zipfile
root=Path.cwd();dest=root.parent.parent/'outputs/XZ-Village-Full-Reconstruction'
assert json.loads((dest/'validation.json').read_text())['passed']
assert json.loads((dest/'browser_review.json').read_text())['passed']
files=sorted(p for p in dest.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(dest))+'\n' for p in files);(dest/'SHA256SUMS.txt').write_text(sums)
zip_path=dest.with_suffix('.zip')
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for p in sorted(dest.rglob('*')):
  if p.is_file():z.write(p,arcname=str(p.relative_to(dest.parent)))
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None;count=len(z.infolist())
sha=hashlib.sha256(zip_path.read_bytes()).hexdigest();zip_path.with_suffix('.zip.sha256').write_text(sha+'  '+zip_path.name+'\n')
print(json.dumps(dict(path=str(zip_path),bytes=zip_path.stat().st_size,entries=count,crc_passed=True,sha256=sha),indent=2))
