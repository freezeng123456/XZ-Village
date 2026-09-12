"""Attempt independent return localisation from raw matches, with audit images."""
import sqlite3,json
from pathlib import Path
import numpy as np,pycolmap,cv2
from aerial_common import load_main
root=Path('work/aerial');main=load_main(root/'sfm');ret=pycolmap.Reconstruction(root/'sfm/sparse/2');db=sqlite3.connect(root/'sfm/database.db');by={};a=json.loads((root/'alignment.json').read_text());R=np.array(a['rotation']);T=np.array(a['translation']);S=a['scale']
for pid,n,data in db.execute('SELECT pair_id,rows,data FROM matches WHERE rows>0'):
 i,j=pid//2147483647,pid%2147483647
 if i in main.images and j in ret.images:ma,rb=main.images[i],ret.images[j];swap=False
 elif j in main.images and i in ret.images:ma,rb=main.images[j],ret.images[i];swap=True
 else:continue
 pairs=np.frombuffer(data,np.uint32).reshape(-1,2)
 if swap:pairs=pairs[:,::-1]
 group=by.setdefault(rb.name,{})
 for ia,ib in pairs:
  pa,pb=ma.points2D[int(ia)],rb.points2D[int(ib)]
  if pa.has_point3D():
   k=(pa.point3D_id,int(ib));entry=group.setdefault(k,[main.points3D[pa.point3D_id].xyz@R.T*S+T,pb.xy,0,ma.name,pa.xy]);entry[2]+=1
out=[]
for name,entries in by.items():
 im=next(i for i in ret.images.values() if i.name==name);cam=ret.cameras[im.camera_id];K=np.array([[cam.params[0],0,800],[0,cam.params[0],450],[0,0,1]],float);D=np.array([cam.params[3],0,0,0,0]);vals=list(entries.values());X=np.array([v[0] for v in vals]);uv=np.array([v[1] for v in vals]);ok,rv,tv,inl=cv2.solvePnPRansac(X,uv,K,D,iterationsCount=20000,reprojectionError=4,confidence=.999,flags=cv2.SOLVEPNP_AP3P)
 if ok:
  ix=inl.ravel();rv,tv=cv2.solvePnPRefineLM(X[ix],uv[ix],K,D,rv,tv);rot=cv2.Rodrigues(rv)[0];C=(-rot.T@tv).ravel();rms=np.sqrt(np.mean(np.sum((cv2.projectPoints(X[ix],rv,tv,K,D)[0].reshape(-1,2)-uv[ix])**2,axis=1)));out.append(dict(name=name,matches=len(vals),inliers=len(ix),rms=float(rms),position=C.tolist(),rotation=rot.tolist(),translation=tv.ravel().tolist(),controls=[dict(world=X[i].tolist(),pixel=uv[i].tolist(),source=vals[i][3],source_uv=vals[i][4].tolist()) for i in ix]));print(name,len(vals),len(ix),rms,C,flush=True)
Path('work/buildings/return_localization_candidates.json').write_text(json.dumps(out,indent=2))
