"""Diagnostic plane-based landmark geometry. All results are unaccepted trials."""
import json
from pathlib import Path
import numpy as np,cv2,pycolmap as pc,open3d as o3d
root=Path('work/rebuild4');out=root/'manual_alignment'
planes=[
 dict(id='red',a=[[100,347],[165,299],[319,308],[260,358]],b=[[580,168],[623,217],[554,222],[503,174]]),
 dict(id='cyan',a=[[550,486],[582,457],[816,473],[788,503]],b=[[612,69],[579,76],[531,32],[564,24]]),
]
offset=[np.array([250,330]),np.array([1460,0])];fits=[];rows=[]
for f,(name,model,t) in enumerate([('pilot_depth_trial',1,44),('return_depth_trial',0,256)]):
 dat=np.load(root/name/'points.npz');xyz=dat['xyz'];rec=pc.Reconstruction(root/f'sfm/sparse_bounded/{model}');im=rec.find_image_with_name(f'frame_{t:06.2f}.jpg');cam=rec.cameras[im.camera_id]
 v=xyz@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation;uv=cam.img_from_cam(v);uv=np.nan_to_num(uv,nan=-1e5);ix=np.round(uv).astype(int)
 vis=(v[:,2]>0)&(ix[:,0]>=0)&(ix[:,1]>=0)&(ix[:,0]<2400)&(ix[:,1]<1350)
 for row in planes:
  poly=np.array(row['a' if f==0 else 'b'])+offset[f];mask=np.zeros((1350,2400),np.uint8);cv2.fillPoly(mask,[poly.astype(np.int32)],255);mask=cv2.erode(mask,np.ones((7,7),np.uint8))
  use=np.where(vis)[0];use=use[mask[ix[use,1],ix[use,0]]>0];X=xyz[use];dep=np.median(v[use,2]);pcl=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(X.astype(float)))
  pl,inlier=pcl.segment_plane(distance_threshold=dep*.0015,ransac_n=3,num_iterations=5000);pl=np.array(pl);selected=X[inlier];center=selected.mean(0);_,_,vt=np.linalg.svd(selected-center);normal=vt[-1];pl=np.r_[normal,-center@normal]
  C=im.projection_center();rays=np.c_[cam.cam_from_img(poly.astype(float)),np.ones(len(poly))]@im.cam_from_world().rotation.matrix();depth=-(C@normal+pl[3])/(rays@normal);corners=C+rays*depth[:,None]
  angles=[]
  for i in range(4):
   aa=corners[(i-1)%4]-corners[i];bb=corners[(i+1)%4]-corners[i];angles.append(float(np.degrees(np.arccos(np.clip(aa@bb/np.linalg.norm(aa)/np.linalg.norm(bb),-1,1)))))
  r=dict(id=row['id'],flight=f,plane=pl.tolist(),selected_points=len(X),inliers=len(inlier),residual=float(np.std(selected@normal+pl[3])),corners=corners.tolist(),angles=angles,projected_pixels=poly.tolist());rows.append(r);print(row['id'],f,'plane',pl,'pts',len(X),len(inlier),'angles',angles,flush=True)
  np.savez(out/f"plane_{row['id']}_{f}.npz",points=X,inliers=inlier,corners=corners)
  fits.append(r)
A=np.array([p for r in rows if r['flight']==0 for p in r['corners']]);B=np.array([p for r in rows if r['flight']==1 for p in r['corners']]);ma,mb=A.mean(0),B.mean(0);aa=A-ma;bb=B-mb;U,d,Vt=np.linalg.svd(aa.T@bb/len(A));S=np.eye(3);S[-1,-1]=np.linalg.det(U@Vt);R=U@S@Vt;s=float(np.sum(d*np.diag(S))/(bb*bb).sum()*len(A));t=ma-s*R@mb;err=np.linalg.norm(s*B@R.T+t-A,axis=1)
result=dict(status='unaccepted_plane_projection_trial',scale=s,R=R.tolist(),t=t.tolist(),rmse=float(np.sqrt(np.mean(err**2))),errors=err.tolist(),planes=rows)
(out/'plane_ties.json').write_text(json.dumps(result,indent=2));print('SIM3',s,result['rmse'],err,flush=True)
