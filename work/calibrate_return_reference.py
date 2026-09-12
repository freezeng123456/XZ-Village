"""Independent manually controlled return-view camera; not a merged SfM result."""
import json,numpy as np,cv2,pycolmap
from pathlib import Path
from aerial_common import load_main
root=Path('work/aerial');main=load_main(root/'sfm');im=next(i for i in main.images.values() if i.name=='f048.00.jpg');cam=main.cameras[im.camera_id];a=json.loads((root/'alignment.json').read_text());R=np.array(a['rotation']);T=np.array(a['translation']);S=a['scale'];C=S*R@im.projection_center()+T
pairs=[[[705,251],[355,200]],[[871,251],[377,115]],[[876,263],[354,116]],[[700,263],[330,200]],[[919,476],[793,84]]]
u=np.array([p[0] for p in pairs],float);d=np.column_stack((cam.cam_from_img(u),np.ones(len(u))))@im.cam_from_world().rotation.matrix()@R.T;xyz=C+d*((.3-C[2])/d[:,2])[:,None]
ret=pycolmap.Reconstruction(root/'sfm/sparse/2');ri=next(i for i in ret.images.values() if i.name=='f256.00.jpg');rc=ret.cameras[ri.camera_id];f=rc.params[0];K=np.array([[f,0,800],[0,f,450],[0,0,1]],float);dist=np.array([rc.params[3],0,0,0,0]);v=np.array([p[1] for p in pairs],float)
ok,rv,tv=cv2.solvePnP(xyz,v,K,dist,flags=cv2.SOLVEPNP_ITERATIVE);rot=cv2.Rodrigues(rv)[0];pred=cv2.projectPoints(xyz,rv,tv,K,dist)[0].reshape(-1,2);res=np.linalg.norm(pred-v,axis=1)
out=dict(rotation_world_to_camera=rot.tolist(),translation_world_to_camera=tv.ravel().tolist(),K=K.tolist(),distortion=dist.tolist(),position=(-rot.T@tv).ravel().tolist(),controls=[dict(main_uv=p[0],return_uv=p[1],world=q.tolist(),residual_px=float(e)) for p,q,e in zip(pairs,xyz,res)],status='manual camera candidate; roof overlap review required; not registered photogrammetry')
Path('work/buildings/return_camera_candidate.json').write_text(json.dumps(out,indent=2));photo=cv2.imread(str(root/'sfm/images/f256.00.jpg'))
roofs=json.loads(Path('work/buildings/architecture_candidates.json').read_text())['buildings']+[dict(id='B001',roof_world=[[0,0,10.65],[7.5,0,10.65],[7.5,9,10.65],[0,9,10.65]])]
for b in roofs:
 world=np.array(b['roof_world']);px=cv2.projectPoints(world,rv,tv,K,dist)[0].reshape(-1,2).astype(int)
 if np.max(np.abs(px))>100000:continue
 cv2.polylines(photo,[px],True,(0,0,255),1);cv2.putText(photo,b['id'],tuple(px.mean(0).astype(int)),cv2.FONT_HERSHEY_SIMPLEX,.4,(255,0,0),1)
cv2.imwrite('work/buildings/return_pnp_overlay.jpg',photo);print('camera',out['position'],'errors',res)
