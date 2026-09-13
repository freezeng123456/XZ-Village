"""Generate genuine image-feature matches after local plane view normalization.

The trial alignment only predicts the search regions. Descriptors must match
the observed photographs, followed by geometric and visual verification.
"""
import cv2,numpy as np,json,time,os,sys
from pathlib import Path
import pycolmap as pc
from scipy.spatial import cKDTree
root=Path('work/rebuild4');learned=os.environ.get('LEARNED','0')=='1';unified=os.environ.get('UNIFIED','0')=='1';time0=int(os.environ.get('PAIR_A','44'));time1=int(os.environ.get('PAIR_B','256'));suffix=f'_{time0:03d}_{time1:03d}' if unified else '';out=root/(('plane_guided_learned' if learned else 'plane_guided_visible')+suffix);out.mkdir(exist_ok=True)
j=json.load(open(root/'manual_alignment/corrected_plane_ties.json'));s=j['scale'];S=np.array(j['R']);t=np.array(j['t'])
r0=pc.Reconstruction(root/('sfm/sparse_unified/0' if unified else 'sfm/sparse_bounded/1'));r1=pc.Reconstruction(root/('sfm/sparse_unified/0' if unified else 'sfm/sparse_bounded/0'));i0=r0.find_image_with_name(f'frame_{time0:06.2f}.jpg');i1=r1.find_image_with_name(f'frame_{time1:06.2f}.jpg');c0=r0.cameras[i0.camera_id];c1=r1.cameras[i1.camera_id]
dat=np.load(root/'outbound_surface/points.npz');xyz=dat['xyz'];norm=dat['normal'];up=np.array([0.,.9,.43])
if unified:
 tr=json.load(open(root/'sfm/component_1_to_unified.json'));rot=np.array(tr['R']);xyz=tr['scale']*xyz@rot.T+tr['t'];norm=norm@rot.T;up=up@rot.T;s=1.;S=np.eye(3);t=np.zeros(3)
v=xyz@i0.cam_from_world().rotation.matrix().T+i0.cam_from_world().translation;uv=c0.img_from_cam(v);uv=np.nan_to_num(uv,nan=-1e5,posinf=1e5,neginf=-1e5)
pix=np.round(np.clip(uv/2,-1e5,1e5)).astype(int);inside=(v[:,2]>0)&(pix[:,0]>=0)&(pix[:,0]<1200)&(pix[:,1]>=0)&(pix[:,1]<675)
zbuf=np.full((675,1200),np.inf,np.float32);ii=np.flatnonzero(inside);np.minimum.at(zbuf,(pix[ii,1],pix[ii,0]),v[ii,2]);zbuf=cv2.erode(zbuf,np.ones((3,3),np.uint8))
visible=np.zeros(len(xyz),bool);visible[ii]=v[ii,2]<=zbuf[pix[ii,1],pix[ii,0]]+v[ii,2]*.004
up/=np.linalg.norm(up);good=(np.abs(norm@up)>.7)&visible
xyz=xyz[good];uv=uv[good];dep=v[good,2]
a=cv2.imread(str(root/f'sfm/images/frame_{time0:06.2f}.jpg'));b=cv2.imread(str(root/f'sfm/images/frame_{time1:06.2f}.jpg'));ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY);gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
sift=cv2.SIFT_create(nfeatures=1500,contrastThreshold=.012,edgeThreshold=16,sigma=1.1);matcher=cv2.FlannBasedMatcher(dict(algorithm=1,trees=4),dict(checks=80));rng=np.random.default_rng(915)
if learned:
 sys.path.insert(0,str((root/'tools/onnx_runtime').resolve()));import onnxruntime as ort
 opts=ort.SessionOptions();opts.intra_op_num_threads=3;opts.inter_op_num_threads=1;net=ort.InferenceSession(str(root/'tools/superpoint_2048_lightglue_end2end.onnx'),sess_options=opts,providers=['CPUExecutionProvider'])
matches=[];patches=[];C=i0.projection_center();R0=i0.cam_from_world().rotation.matrix();start=time.time()
for y in range(270,1240,110):
 for x in range(0,1550,160):
  lo=np.array([x,y]);hi=lo+[220,170];idx=np.flatnonzero(np.all(uv>=lo,axis=1)&np.all(uv<hi,axis=1))
  if len(idx)<35:continue
  X=xyz[idx];depth=np.median(dep[idx]);threshold=depth*.002;best=[];plane=None
  for _ in range(200):
   q=X[rng.choice(len(X),3,replace=False)];n=np.cross(q[1]-q[0],q[2]-q[0]);ln=np.linalg.norm(n)
   if ln<1e-9:continue
   n/=ln
   if abs(n@up)<.7:continue
   d=-q[0]@n;ids=np.flatnonzero(np.abs(X@n+d)<threshold)
   if len(ids)>len(best):best=ids;plane=(n,d)
  if len(best)<30:continue
  xx=X[best];center=xx.mean(0);_,_,vt=np.linalg.svd(xx-center);n=vt[-1];d=-center@n
  corners=np.float32([lo,lo+[220,0],hi,lo+[0,170]]);rays=np.c_[c0.cam_from_img(corners.astype(float)),np.ones(4)]@R0;z=-(C@n+d)/(rays@n);W=C+rays*z[:,None];W=(W-t)@S/s;V=W@i1.cam_from_world().rotation.matrix().T+i1.cam_from_world().translation;q=c1.img_from_cam(V)
  if np.any(V[:,2]<=0) or not np.isfinite(q).all() or q[:,0].max()<0 or q[:,1].max()<0 or q[:,0].min()>=2400 or q[:,1].min()>=1350:continue
  H=cv2.getPerspectiveTransform(corners,q.astype(np.float32));pad=35;xl=max(0,x-pad);yl=max(0,y-pad);xr=min(2400,x+220+pad);yr=min(1350,y+170+pad);T=np.array([[1.,0,-xl],[0,1.,-yl],[0,0,1.]])
  back=cv2.warpPerspective(gb,T@np.linalg.inv(H),(xr-xl,yr-yl));crop=ga[yl:yr,xl:xr];pmask=np.zeros_like(crop)
  pp=np.round(uv[idx[best]]-[xl,yl]).astype(int);pmask[pp[:,1],pp[:,0]]=255;pmask=cv2.dilate(pmask,np.ones((11,11),np.uint8))
  if learned:
   hh,ww=crop.shape;sw=ww*2//8*8;sh=hh*2//8*8;sc=np.array([sw/ww,sh/hh]);aa=cv2.resize(crop,(sw,sh))[None,None].astype(np.float32)/255;bb=cv2.resize(back,(sw,sh))[None,None].astype(np.float32)/255
   kk0,kk1,mm0,mm1,ss0,ss1=net.run(None,{'image0':aa,'image1':bb});ok=(mm0[0]>=0)&(ss0[0]>.15);ii=np.flatnonzero(ok);jj=mm0[0][ok];kp0=(kk0[0][ii]+.5)/sc-.5;kp1=(kk1[0][jj]+.5)/sc-.5;count=0
   for p0,p1,score in zip(kp0,kp1,ss0[0][ok]):
    px=np.round(p0).astype(int)
    if not(0<=px[0]<ww and 0<=px[1]<hh and pmask[px[1],px[0]]>0) or np.linalg.norm(p0-p1)>55:continue
    p=p0+[xl,yl];p1=p1+[xl,yl];q1=cv2.perspectiveTransform(p1.astype(np.float32).reshape(1,1,2),H).ravel()
    if not(3<=q1[0]<2397 and 3<=q1[1]<1347):continue
    matches.append(dict(p=p.tolist(),q=q1.tolist(),ratio=float(1-score),patch=[x,y]));count+=1
   patches.append(dict(x=x,y=y,inlier_points=len(best),features=len(kk0[0]),matches=count))
   if count>=4:cv2.imwrite(str(out/f'patch_{x}_{y}.jpg'),np.hstack([crop,back]))
   print('PATCH',x,y,len(best),len(kk0[0]),count,flush=True);continue
  k0,d0=sift.detectAndCompute(crop,pmask);k1,d1=sift.detectAndCompute(back,None)
  if d0 is None or d1 is None or len(d1)<2:continue
  pairs=matcher.knnMatch(d0,d1,k=2);rev=matcher.match(d1,d0);rev={m.queryIdx:m.trainIdx for m in rev};count=0
  for m,nn in pairs:
   if m.distance>=.86*nn.distance or rev.get(m.trainIdx)!=m.queryIdx:continue
   p=np.array(k0[m.queryIdx].pt)+[xl,yl];p1=np.array(k1[m.trainIdx].pt)+[xl,yl]
   if np.linalg.norm(p-p1)>55:continue
   q1=cv2.perspectiveTransform(p1.astype(np.float32).reshape(1,1,2),H).ravel()
   if not(3<=q1[0]<2397 and 3<=q1[1]<1347):continue
   matches.append(dict(p=p.tolist(),q=q1.tolist(),ratio=float(m.distance/nn.distance),patch=[x,y]));count+=1
  patches.append(dict(x=x,y=y,inlier_points=len(best),features=len(k0),matches=count))
  if count>=4:cv2.imwrite(str(out/f'patch_{x}_{y}.jpg'),np.hstack([crop,back]))
  print('PATCH',x,y,len(best),len(k0),count,flush=True)
if not matches:raise RuntimeError('No plane-normalized image matches')
# Keep unique image-feature pairs; overlapping search patches are not extra evidence.
matches.sort(key=lambda m:m['ratio']);kept=[]
for m in matches:
 if any(np.linalg.norm(np.array(m['p'])-k['p'])<3 and np.linalg.norm(np.array(m['q'])-k['q'])<3 for k in kept):continue
 kept.append(m)
p=np.float32([m['p'] for m in kept]);q=np.float32([m['q'] for m in kept]);F,mask=cv2.findFundamentalMat(p,q,cv2.USAC_MAGSAC,2.5,.9999,100000)
mask=mask.ravel()>0 if mask is not None else np.zeros(len(p),bool)
np.savez(out/'matches.npz',p=p,q=q,inlier=mask,F=F)
(out/'raw_matches.json').write_text(json.dumps(kept,indent=2));summary=dict(status='unaccepted_image_matches',time0=time0,time1=time1,unified_pose_trial=unified,raw=len(matches),unique=len(kept),fundamental_inliers=int(mask.sum()),patches=patches,elapsed=time.time()-start)
mat=np.c_[np.arange(len(p)),np.arange(len(p))].astype(np.uint32);g=pc.estimate_calibrated_two_view_geometry(c0,np.ascontiguousarray(p,dtype=np.float64),c1,np.ascontiguousarray(q,dtype=np.float64),mat,pc.TwoViewGeometryOptions(dict(compute_relative_pose=True,ransac=dict(max_error=3,min_inlier_ratio=.1,max_num_trials=100000,random_seed=915))))
np.savez(out/'calibrated_matches.npz',p=p,q=q,matches=g.inlier_matches);summary['calibrated_inliers']=len(g.inlier_matches);(out/'summary.json').write_text(json.dumps(summary,indent=2))
canvas=np.hstack([a,b]);rng=np.random.default_rng(15)
for u,v in zip(p[mask],q[mask]):
 co=tuple(int(c) for c in rng.integers(30,255,3));cv2.line(canvas,tuple(u.astype(int)),tuple((v+[2400,0]).astype(int)),co,2);cv2.circle(canvas,tuple(u.astype(int)),5,co,-1);cv2.circle(canvas,tuple((v+[2400,0]).astype(int)),5,co,-1)
cv2.imwrite(str(out/'inlier_overview.jpg'),cv2.resize(canvas,(2400,675)))
print('GUIDED_DONE',len(kept),int(mask.sum()),time.time()-start,flush=True)
