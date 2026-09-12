"""Select the connected reconstruction containing the 48-second landmark."""
import json
from pathlib import Path
import pycolmap

def main_model_path(root):
    root=Path(root)
    summary=json.loads((root/'summary.json').read_text())
    candidates=[m for m in summary['models'] if 'f048.00.jpg' in m['image_names']]
    if not candidates:raise RuntimeError('No recovered model contains the landmark at 48 seconds')
    primary=max(candidates,key=lambda m:m['registered'])
    return root/'sparse'/str(primary['id'])

def load_main(root):return pycolmap.Reconstruction(main_model_path(root))
