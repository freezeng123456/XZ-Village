"""Localize genuinely withheld video frames with fixed fitted intrinsics.

This tests nearby unseen-image consistency, not survey accuracy or architecture.
"""
import json,time
from pathlib import Path
import numpy as np,cv2,pycolmap as pc
root=Path('work/rebuild4');out=root/'holdout';r=pc.Reconstruction(root/'sfm/sparse_final/0');db=pc.Database.open(root/'sfm/bridge_full.db');hd=pc.Database.open(out/'features.db');images=[im for im in r.images.values() if im.has_pose];cam=r.cameras[1];rows=[];refcache={}
def reference(im):
 if im.image_id not in refcache:
  d=np.asarray(db.read_descriptors(im.image_id).data);idx=np.array([i for i,p in enumerate(im.points2D) if p.has_point3D() and i<len(d) and d[i].any()]);desc=d[idx].astype(np.float32);ids=np.array([im.points2D[i].point3D_id for i in idx]);refcache[im.image_id]=(desc,ids)
 return refcache[im.image_id]
for image in hd.read_all_images():
 t=float(image.name[8:-4]);start=time.time();kp=hd.read_keypoints(image.image_id)[:,:2];desc=np.asarray(hd.read_descriptors(image.image_id).data).astype(np.float32);near=sorted(images,key=lambda im:abs(float(im.name[6:-4])-t))[:4];candidate={}
 for im in near:
  rd,rids=reference(im);matcher=cv2.FlannBasedMatcher(dict(algorithm=1,trees=4),dict(checks=80));matches=matcher.knnMatch(desc,rd,k=2)
  for a,b in matches:
   ratio=a.distance/max(1e-9,b.distance)
   if ratio>.76:continue
   if a.queryIdx not in candidate or ratio<candidate[a.queryIdx][0]:candidate[a.queryIdx]=(ratio,int(rids[a.trainIdx]))
 selected=[];seen=set()
 for qi,(ratio,id3) in sorted(candidate.items(),key=lambda kv:kv[1][0]):
  if id3 in seen:continue
  seen.add(id3);selected.append((qi,id3,ratio))
 xy=np.array([kp[i] for i,_,_ in selected],np.float64);X=np.array([r.points3D[j].xyz for _,j,_ in selected],np.float64)
 opts=pc.AbsolutePoseEstimationOptions(dict(ransac=dict(max_error=3,min_inlier_ratio=.1,confidence=.9999,max_num_trials=20000,random_seed=917)))
 result=pc.estimate_and_refine_absolute_pose(xy,X,cam,opts,pc.AbsolutePoseRefinementOptions(dict(refine_focal_length=False,refine_extra_params=False)))
 if result is None:rows.append(dict(image=image.name,status='failed',matches=len(xy)));continue
 pose=result['cam_from_world'];inlier_values=result.get('inlier_mask',result.get('inliers'))
 if inlier_values is None:raise RuntimeError(f'Unknown pose result keys: {list(result)}')
 mask=np.asarray(inlier_values,bool);v=X@pose.rotation.matrix().T+pose.translation;projected=cam.img_from_cam(v);err=np.linalg.norm(projected-xy,axis=1);bins=np.unique(np.floor(xy[mask]/[300,225]).astype(int),axis=0)
 row=dict(image=image.name,not_used_in_sfm_or_bundle_adjustment=True,pose_fitted_to_existing_3d=True,intrinsics_fixed=True,feature_matches=len(xy),pose_inliers=int(mask.sum()),median_error_px=float(np.median(err[mask])),p95_error_px=float(np.percentile(err[mask],95)),covered_300x225_bins=len(bins),R=pose.rotation.matrix().tolist(),T=pose.translation.tolist(),reference_images=[im.name for im in near],elapsed_seconds=time.time()-start)
 row['numerical_gate']=bool(row['pose_inliers']>=100 and row['median_error_px']<1.2 and row['p95_error_px']<3 and len(bins)>=12);rows.append(row);print({k:v for k,v in row.items() if k not in ['R','T']},flush=True)
 im=cv2.imread(str(out/image.name))
 for p in xy[mask]:cv2.circle(im,tuple(np.round(p).astype(int)),3,(0,200,255),-1)
 cv2.imwrite(str(out/(Path(image.name).stem+'_inliers.jpg')),im);np.savez(out/(Path(image.name).stem+'_observations.npz'),xy=xy,xyz=X,inliers=mask,reprojection_error=err)
db.close();hd.close();(out/'audit.json').write_text(json.dumps(dict(scope='Near-time withheld-image consistency only; not independent survey ground truth or model completeness',frames=rows,all_numerical_gates_passed=bool(len(rows)==6 and all(x.get('numerical_gate',False) for x in rows))),indent=2))
