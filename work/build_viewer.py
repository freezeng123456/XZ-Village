"""Make a self-contained browser preview with deterministic point sampling."""
import base64,json
from pathlib import Path
import numpy as np
z=np.load('work/aerial/package/cloud.npz');xyz=z['xyz'];rgb=z['rgb']
rng=np.random.default_rng(216);ids=np.sort(rng.choice(len(xyz),min(350000,len(xyz)),replace=False));xyz=xyz[ids];rgb=rgb[ids]
minimum=xyz.min(axis=0);span=xyz.max(axis=0)-minimum
packed=np.round((xyz-minimum)/span*65535).astype('<u2').tobytes()+rgb.tobytes()
html=Path('work/viewer_template.html').read_text().replace('__DATA__',base64.b64encode(packed).decode()).replace('__COUNT__',str(len(xyz))).replace('__MIN__',json.dumps(minimum.tolist())).replace('__SPAN__',json.dumps(span.tolist()))
html=html.replace('distance=345','distance=460').replace('distance=360','distance=500')
summary=json.loads(Path('work/aerial/package/summary.json').read_text())
html=html.replace('1,003,368',f"{summary['cloud_points']:,}").replace('1,631,407',f"{summary['triangles']:,}")
html=html.replace('</style>','main{height:calc(100dvh - 113px);min-height:0}.stage{min-height:0;height:100%}.aside{overflow-y:auto}@media(max-width:850px){main{height:auto}.stage{height:62vh;min-height:420px}.aside{overflow:visible}}</style>')
out=Path('outputs/aerial-continuation/Village_Viewer.html');out.write_text(html)
print(out, out.stat().st_size)
