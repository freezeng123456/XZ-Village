import json,numpy as np,pycolmap,cv2
from pathlib import Path
from aerial_common import load_main
root=Path('work/aerial');ret=pycolmap.Reconstruction(root/'sfm/sparse/2');im=next(i for i in ret.images.values() if i.name=='f256.00.jpg');cam=ret.cameras[im.camera_id];RC=im.cam_from_world().rotation.matrix();C=im.projection_center()
road=np.array([[340,105],[845,23],[857,47],[353,128]],np.float32)
ps=[ret.points3D[p.point3D_id].xyz for p in im.points2D if p.has_point3D() and cv2.pointPolygonTest(road,tuple(p.xy),False)>0];X=np.array(ps)
rng=np.random.default_rng(19);best=np.zeros(len(X),bool)
for _ in range(1000):
 q=X[rng.choice(len(X),3,False)];n=np.cross(q[1]-q[0],q[2]-q[0]);n/=np.linalg.norm(n);mask=np.abs((X-q[0])@n)<.025
 if mask.sum()>best.sum():best=mask
p=X[best].mean(0);_,_,vt=np.linalg.svd(X[best]-p);n=vt[-1]
if n@(C-p)<0:n=-n
def intersect(uv):
 d=np.column_stack((cam.cam_from_img(np.array(uv,float)),np.ones(len(uv))))@RC;return C+d*(((p-C)@n)/(d@n))[:,None]
q=intersect([[331,200],[354,116],[793,84]])
main=load_main(root/'sfm');mi=next(i for i in main.images.values() if i.name=='f048.00.jpg');mc=main.cameras[mi.camera_id];a=json.loads((root/'alignment.json').read_text());AR=np.array(a['rotation']);AT=np.array(a['translation']);AS=a['scale'];MC=AS*AR@mi.projection_center()+AT
uv=np.array([[705,259],[876,263],[919,476]],float);d=np.column_stack((mc.cam_from_img(uv),np.ones(3)))@mi.cam_from_world().rotation.matrix()@AR.T;y=MC+d*((.3-MC[2])/d[:,2])[:,None]
xc=q-q.mean(0);yc=y-y.mean(0);u,ss,v=np.linalg.svd(yc.T@xc);D=np.eye(3);D[2,2]=np.linalg.det(u@v);R=u@D@v;s=np.trace(np.diag(ss)@D)/(xc*xc).sum();t=y.mean(0)-s*R@q.mean(0)
out=dict(scale=float(s),rotation=R.tolist(),translation=t.tolist(),ground_points=len(X),ground_inliers=int(best.sum()),controls_residual_nominal_m=np.linalg.norm(s*q@R.T+t-y,axis=1).tolist(),status='manual ground-plane candidate; requires roof overlay review')
Path('work/buildings/return_alignment_candidate.json').write_text(json.dumps(out,indent=2))
photo=cv2.imread(str(root/'sfm/images/f256.00.jpg'))
roofs=json.loads((root/'package/neighbour_roofs.json').read_text())+[dict(name='TARGET',roof_vertices=[[0,0,10.65],[7.5,0,10.65],[7.5,9,10.65],[0,9,10.65]])]
for k,b in enumerate(roofs):
 world=np.array(b['roof_vertices']);raw=(world-t)@R/s;pc=raw@RC.T+im.cam_from_world().translation;px=cam.img_from_cam(pc);px=px.astype(int);cv2.polylines(photo,[px],True,(0,0,255),2);cv2.putText(photo,str(k),tuple(px.mean(0).astype(int)),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,0,0),2)
cv2.imwrite('work/buildings/return_roof_overlay.jpg',photo);print(json.dumps(out,indent=2))
