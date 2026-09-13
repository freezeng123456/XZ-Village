"""Align saved depth references using unchanged SIFT observation indices.

Appended learned points make COLMAP's same-length image assertion unsuitable;
only the original prefix of each image is compared here.
"""
import json,os
from pathlib import Path
import numpy as np,pycolmap as pc
root=Path('work/rebuild4');label=os.environ.get('ALIGN_TARGET','unified');new=pc.Reconstruction(root/f'sfm/sparse_{label}/0')
def fit(A,B):
 ma,mb=A.mean(0),B.mean(0);aa=A-ma;bb=B-mb;U,d,Vt=np.linalg.svd(bb.T@aa/len(A));S=np.eye(3);S[-1,-1]=np.linalg.det(U@Vt);R=U@S@Vt;s=float(np.sum(d*np.diag(S))/(aa*aa).sum()*len(A));t=mb-s*R@ma;return s,R,t
for component in [0,1]:
 old=pc.Reconstruction(root/f'sfm/sparse_bounded/{component}');pairs={}
 for iid,im in old.images.items():
  if not im.has_pose or not new.exists_image(iid):continue
  target=new.images[iid]
  if not target.has_pose:continue
  for i,pt in enumerate(im.points2D):
   if pt.has_point3D() and target.points2D[i].has_point3D():pairs[pt.point3D_id]=(old.points3D[pt.point3D_id].xyz,new.points3D[target.points2D[i].point3D_id].xyz)
 A=np.array([v[0] for v in pairs.values()]);B=np.array([v[1] for v in pairs.values()]);use=np.arange(len(A))
 for _ in range(8):
  s,R,t=fit(A[use],B[use]);err=np.linalg.norm(s*A@R.T+t-B,axis=1);use=np.flatnonzero(err<np.percentile(err,85))
 result=dict(scale=s,R=R.tolist(),t=t.tolist(),matched_points=len(A),retained_points=len(use),median_error=float(np.median(err)),p90_error=float(np.percentile(err,90)),alignment_purpose='transform geometric reference only; not a new camera verification')
 (root/f'sfm/component_{component}_to_{label}.json').write_text(json.dumps(result,indent=2));print(component,result,flush=True)
