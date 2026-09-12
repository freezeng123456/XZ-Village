"""Manual 48-second shoreline tracing; depths/heights remain estimates."""
import json,numpy as np,pycolmap
from pathlib import Path
from aerial_common import load_main
root=Path('work/aerial');al=json.loads((root/'alignment.json').read_text())
R=np.array(al['rotation']);t=np.array(al['translation']);s=al['scale']
r=load_main(root/'sfm');im=next(i for i in r.images.values() if i.name=='f048.00.jpg');cam=r.cameras[im.camera_id]
C=s*R@im.projection_center()+t
def trace(name,px,z,kind,certainty):
    xy=cam.cam_from_img(np.array(px,float));rays=np.column_stack((xy,np.ones(len(xy))))@im.cam_from_world().rotation.matrix()@R.T
    p=C+rays*((z-C[2])/rays[:,2])[:,None]
    return dict(name=name,pixels=px,vertices=p.tolist(),kind=kind,evidence=certainty,nominal_z=z)
items=[
trace('Main pond water',[[698,264],[872,265],[920,480],[905,484],[880,476],[858,455],[840,420],[826,386],[794,384],[772,392],[624,329],[627,313],[650,292],[679,274]],-.55,'water',
      'Visible shoreline manually traced at 48s; left boundary under buildings interpolated. Water elevation is assumed, not measured.'),
trace('Visible east pond railing',[[874,264],[883,317],[899,384],[920,480],[905,484],[880,476],[858,455],[840,420],[826,386],[794,384]],.1,'rail',
      'Visible red railing path traced from 48s. Railing height and section size estimated.'),
trace('Visible northwest pond railing',[[625,314],[650,292],[679,274],[700,258]],.1,'rail',
      'Visible bank path; no invented continuation behind occluding buildings.'),
trace('Pond cross bridge',[[704,251],[871,253]],.25,'bridge',
      'Bridge centreline traced; deck width and elevation are estimates.'),
]
(root/'package/site_traces.json').write_text(json.dumps(items,indent=2)+'\n')
print(json.dumps(items,indent=2))
