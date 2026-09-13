from pathlib import Path
import base64,shutil
R=Path('work/rebuild4/viewer');P=Path('work/rebuild4/architecture');O=Path('/Users/zenghang/Documents/Codex/2026-09-12/jie/outputs/XZ-Village-Rebuilt-V4');D=R/'node_modules/three/examples/jsm/libs/draco/gltf';s=(R/'template.html').read_text()
for key,val in {'METADATA':(O/'data/viewer_metadata.json').read_text(),'MODEL':base64.b64encode((P/'web/Village_Rebuilt_Web.glb').read_bytes()).decode(),'WASM':base64.b64encode((D/'draco_decoder.wasm').read_bytes()).decode(),'DRACO':(D/'draco_wasm_wrapper.js').read_text(),'APP':(R/'app.bundle.js').read_text()}.items():s=s.replace('__'+key+'__',val)
(O/'Village_Viewer.html').write_text(s);shutil.copy2(P/'web/Village_Rebuilt_Web.glb',O/'Village_Rebuilt_Web.glb');print('VIEWER_BYTES',(O/'Village_Viewer.html').stat().st_size)
