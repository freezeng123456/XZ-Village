import json,numpy as np,cv2
from pathlib import Path
from aerial_common import load_main
r=load_main('work/aerial/sfm');a=json.loads(Path('work/aerial/alignment.json').read_text());R=np.array(a['rotation']);T=np.array(a['translation']);S=a['scale'];buildings=json.loads(Path('work/buildings/architecture_candidates.json').read_text())['buildings']
buildings.append(dict(id='B001',t=48,roof_world=[[0,0,10.65],[7.5,0,10.65],[7.5,8.5,10.65],[0,8.5,10.65]]))
for ts in [0,20,44,76,88,104]:
 im=next(i for i in r.images.values() if i.name==f'f{ts:06.2f}.jpg');cam=r.cameras[im.camera_id];cr=im.cam_from_world().rotation.matrix();ct=im.cam_from_world().translation;src=cv2.imread(f'work/aerial/sfm/images/{im.name}')
 for b in buildings:
  raw=(np.array(b['roof_world'])-T)@R/S;px=cam.img_from_cam(raw@cr.T+ct)
  if not np.isfinite(px).all() or np.max(np.abs(px))>4000:continue
  px=px.astype(int);col=(0,220,255) if b['t']!=256 else (100,220,0);cv2.polylines(src,[px],True,col,1);cv2.putText(src,b['id'],tuple(px.mean(0).astype(int)),cv2.FONT_HERSHEY_SIMPLEX,.3,col,1)
 cv2.imwrite(f'work/buildings/all_projection_{ts:03}.jpg',src)
 if ts==44:cv2.imwrite('work/buildings/north_coverage_crop.jpg',cv2.resize(src[:180,:620],None,fx=2,fy=2))
