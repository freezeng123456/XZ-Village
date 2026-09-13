"""Trace explicit same-corner hypotheses within each flight and test a similarity fit.

This is an evidence trial, not an accepted registration. Save every observation,
reprojection residual and visual comparison before using the transform.
"""
import json
from pathlib import Path
import cv2,numpy as np,pycolmap as pc
from scipy.optimize import least_squares

root=Path('work/rebuild4');out=root/'manual_alignment';out.mkdir(exist_ok=True)
ties=[
 ('red_A',(100,347),(580,168)),
 ('red_B',(165,299),(623,217)),
 ('red_C',(319,308),(554,222)),
 ('cyan_A',(550,486),(612,69)),
 ('cyan_B',(582,457),(579,76)),
 ('cyan_C',(816,473),(531,32)),
 ('cyan_D',(788,503),(564,24)),
]
offset=[np.array([250,330]),np.array([1460,0])]
rec=[pc.Reconstruction(root/'sfm/sparse_bounded/1'),pc.Reconstruction(root/'sfm/sparse_bounded/0')]
cache={}
def photo(t):
 name=f'frame_{t:06.2f}.jpg'
 if name not in cache:cache[name]=cv2.imread(str(root/'sfm/images'/name),cv2.IMREAD_GRAYSCALE)
 return cache[name]
def camera(f,t):
 im=rec[f].find_image_with_name(f'frame_{t:06.2f}.jpg');c=rec[f].cameras[im.camera_id]
 return im,c
def project(X,im,c):
 v=np.asarray(X)@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation
 return c.img_from_cam(v)
def track_corner(f,xy):
 t0=44 if f==0 else 256;step=2 if f==0 else 1
 lo,hi=(22,68) if f==0 else (244,268)
 p0=np.array(xy,np.float32).reshape(1,1,2)
 im0,c0=camera(f,t0);near=[]
 for pt in im0.points2D:
  if not pt.has_point3D():continue
  dist=np.linalg.norm(pt.xy-xy)
  zz=(im0.cam_from_world()*rec[f].points3D[pt.point3D_id].xyz)[2]
  if zz>0:near.append((dist,zz))
 near.sort();depth=np.median([z for _,z in near[:3]])
 ray=np.r_[c0.cam_from_img(np.array(xy)),1.]
 seed=im0.cam_from_world().rotation.matrix().T@(depth*ray-im0.cam_from_world().translation)
 # Keep the declared landmark fixed. Do not snap it to a different nearby corner.
 obs=[dict(time=t0,xy=np.asarray(xy).tolist(),fb_error=0.,lk_error=0.)]
 for sign in [-1,1]:
  prev=t0;p=p0.copy()
  for t in range(t0+sign*step,(hi+1 if sign>0 else lo-1),sign*step):
   predicted=project(seed,*camera(f,t))+p.ravel()-project(seed,*camera(f,prev))
   candidates=[]
   for win in [15,25,41]:
    nxt,st,err=cv2.calcOpticalFlowPyrLK(photo(prev),photo(t),p,predicted.astype(np.float32).reshape(1,1,2),winSize=(win,win),maxLevel=5,flags=cv2.OPTFLOW_USE_INITIAL_FLOW,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.001))
    if not st[0,0] or np.linalg.norm(nxt.ravel()-predicted)>80:continue
    ip,cp=camera(f,prev);it,ct=camera(f,t);rel=it.cam_from_world()*ip.cam_from_world().inverse();u=np.r_[cp.cam_from_img(p.ravel().astype(float)),1.];v=np.r_[ct.cam_from_img(nxt.ravel().astype(float)),1.]
    line=np.cross(rel.translation,rel.rotation.matrix()@u);epi=abs(v@line)/max(1e-12,np.linalg.norm(line[:2]))*ct.focal_length
    if epi>3:continue
    rev,st2,_=cv2.calcOpticalFlowPyrLK(photo(t),photo(prev),nxt,p.copy(),winSize=(win,win),maxLevel=5,flags=cv2.OPTFLOW_USE_INITIAL_FLOW,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.001))
    fb=float(np.linalg.norm(rev-p))
    if st2[0,0] and fb<=2 and err[0,0]<=45:candidates.append((float(err[0,0])+20*fb,nxt,err,fb))
   if not candidates:break
   _,nxt,err,fb=min(candidates,key=lambda z:z[0])
   obs.append(dict(time=t,xy=nxt[0,0].tolist(),fb_error=fb,lk_error=float(err[0,0])))
   prev=t;p=nxt
 mats=[]
 for o in obs:
  im,c=camera(f,o['time']);x,y=c.cam_from_img(np.array(o['xy']));P=im.cam_from_world().matrix()
  mats.extend([x*P[2]-P[0],y*P[2]-P[1]])
 _,_,vt=np.linalg.svd(mats);X=vt[-1,:3]/vt[-1,3]
 def residual(X,indices):
  return np.concatenate([project(X,*camera(f,obs[i]['time']))-obs[i]['xy'] for i in indices])
 ix=list(range(len(obs)))
 for _ in range(3):
  fit=least_squares(residual,X,args=(ix,),loss='soft_l1',f_scale=1.0);X=fit.x
  err=np.linalg.norm(residual(X,list(range(len(obs)))).reshape(-1,2),axis=1)
  ix=np.flatnonzero(err<2.5).tolist()
  if len(ix)<3:break
 for i,o in enumerate(obs):o['reprojection_error']=float(err[i]);o['used']=i in ix
 centers=np.array([camera(f,obs[i]['time'])[0].projection_center() for i in ix]);dirs=centers-X;dirs/=np.linalg.norm(dirs,axis=1,keepdims=True)
 angle=float(np.degrees(np.arccos(np.clip((dirs@dirs.T).min(),-1,1)))) if len(dirs) else 0
 return dict(xyz=X.tolist(),observations=obs,used_observations=len(ix),rmse=float(np.sqrt(np.mean(err[ix]**2))) if ix else None,triangulation_angle_deg=angle)

rows=[]
for id,a,b in ties:
 row=dict(id=id,status='unaccepted_manual_correspondence_hypothesis',pixels=[(np.array(a)+offset[0]).tolist(),(np.array(b)+offset[1]).tolist()])
 row['tracks']=[track_corner(f,row['pixels'][f]) for f in [0,1]];rows.append(row)
 print(id,[(r['used_observations'],r['rmse'],r['triangulation_angle_deg']) for r in row['tracks']],flush=True)

def sim3(A,B): # B to A
 ma,mb=A.mean(0),B.mean(0);aa=A-ma;bb=B-mb
 U,d,Vt=np.linalg.svd(aa.T@bb/len(A));S=np.eye(3);S[-1,-1]=np.linalg.det(U@Vt);R=U@S@Vt
 scale=float(np.sum(d*np.diag(S))/(bb*bb).sum()*len(A));t=ma-scale*R@mb
 return scale,R,t
valid=[r for r in rows if all(t['used_observations']>=3 and t['triangulation_angle_deg']>=2 for t in r['tracks'])]
if len(valid)<3:
 (out/'failed_ties.json').write_text(json.dumps(rows,indent=2));raise RuntimeError('Fewer than three eligible 3D landmark correspondences')
A=np.array([r['tracks'][0]['xyz'] for r in valid]);B=np.array([r['tracks'][1]['xyz'] for r in valid]);scale,R,t=sim3(A,B)
pred=scale*B@R.T+t;err=np.linalg.norm(pred-A,axis=1)
for row,e in zip(valid,err):row['alignment_error_sfm_units']=float(e)
result=dict(status='unaccepted_trial',scale=scale,R=R.tolist(),t=t.tolist(),rmse=float(np.sqrt(np.mean(err**2))),used_anchor_ids=[r['id'] for r in valid],anchors=rows)
(out/'initial_ties.json').write_text(json.dumps(result,indent=2));print('SIMILARITY',scale,'RMSE',result['rmse'],'ERR',err,flush=True)
# A projected into return view after fitted transform: initial error is visible.
imgs=[cv2.imread(str(root/'sfm/images'/f'frame_{t:06.2f}.jpg')) for t in [44,256]]
for j,row in enumerate(rows):
 for f in [0,1]:
  p=np.round(row['pixels'][f]).astype(int);cv2.circle(imgs[f],tuple(p),7,(0,220,255),2);cv2.putText(imgs[f],str(j+1),tuple(p+[8,-8]),cv2.FONT_HERSHEY_SIMPLEX,.65,(0,220,255),2)
 q=project((np.array(row['tracks'][0]['xyz'])-t)@R/scale,*camera(1,256));cv2.drawMarker(imgs[1],tuple(np.round(q).astype(int)),(255,0,255),cv2.MARKER_CROSS,16,2)
for f,im in enumerate(imgs):cv2.imwrite(str(out/f'anchors_{f}.jpg'),im)
