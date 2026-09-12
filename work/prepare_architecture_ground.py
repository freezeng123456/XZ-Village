"""Estimated continuous ground for inspecting roof-constrained architecture.

Heights interpolate explicitly estimated building bases. Source imagery is
assigned only where the architecture visibility buffer reports no building.
This terrain is contextual and is not a recovered or surveyed ground model.
"""
from pathlib import Path
import json,numpy as np,cv2
from scipy.spatial import cKDTree
root=Path('work/buildings');data=json.loads((root/'visibility/architecture_visibility.json').read_text());bs=data['buildings'];anchors=np.array(json.loads((root/'ground_anchors_estimated.json').read_text()));poses=json.loads((root/'visibility/poses.json').read_text());traces=json.loads(Path('work/aerial/package/site_traces.json').read_text());pond=next(np.array(t['vertices']) for t in traces if t['kind']=='water')
anchors=np.vstack([anchors,pond,[[15,y,0] for y in range(-170,211,20)]]);tree=cKDTree(anchors[:,:2]);centers=np.array([np.array(b['roof_world']).mean(0) for b in bs]);ctree=cKDTree(centers[:,:2]);allp=np.vstack([b['roof_world'] for b in bs]);xmin,ymin=allp[:,:2].min(0)-22;xmax,ymax=allp[:,:2].max(0)+22;xs=np.arange(xmin,xmax,3.5);ys=np.arange(ymin,ymax,3.5);xx,yy=np.meshgrid(xs,ys);xy=np.c_[xx.ravel(),yy.ravel()];dist,ix=tree.query(xy,k=8);weights=1/np.maximum(dist,3)**2;zz=np.sum(weights*anchors[ix,2],axis=1)/weights.sum(1)-.05;verts=np.c_[xy,zz]
# Flatten the pad under each explicitly estimated building footprint.
for b in bs:
 p=np.array(b['roof_world'])[:,:2];lo=p.min(0)-.1;hi=p.max(0)+.1;sel=np.flatnonzero(np.all((xy>=lo)&(xy<=hi),axis=1));poly=np.ascontiguousarray(p,np.float32)
 for j in sel:
  if cv2.pointPolygonTest(poly,tuple(xy[j]),False)>=0:verts[j,2]=b['base_height']-.06
nx=len(xs);ny=len(ys);faces=[]
for iy in range(ny-1):
 for j in range(nx-1):
  k=iy*nx+j
  for f in [(k,k+1,k+nx+1),(k,k+nx+1,k+nx)]:
   c=verts[list(f)].mean(0)
   if ctree.query(c[:2])[0]>42:continue
   if cv2.pointPolygonTest(np.ascontiguousarray(pond[:,:2],np.float32),tuple(c[:2]),False)>=0:continue
   faces.append(f)
faces=np.array(faces,np.int32);mid=verts[faces].mean(1);best=np.zeros(len(faces));mats=np.zeros(len(faces),np.int32);uv=np.zeros((len(faces),3,2),np.float32);times=[int(k) for k in poses]
for mi,ts in enumerate(times,1):
 p=poses[str(ts)];R=np.array(p['rotation']);T=np.array(p['translation']);f=p['focal'];rad=p['radial'];K=np.array([[f,0,800],[0,f,450],[0,0,1]],float);D=np.array([rad,0,0,0,0]);rv=cv2.Rodrigues(R)[0];px=cv2.projectPoints(mid,rv,T,K,D)[0].reshape(-1,2);pc=mid@R.T+T;inside=(pc[:,2]>1)&np.isfinite(px).all(1)&(px[:,0]>3)&(px[:,0]<1596)&(px[:,1]>120)&(px[:,1]<896);which=np.flatnonzero(inside);pix=px[which].astype(int);ids=cv2.imread(str(root/f'visibility/face_ids_{ts:03}.png'),cv2.IMREAD_UNCHANGED);ok=ids[pix[:,1],pix[:,0]]==0;which=which[ok];score=f/pc[which,2];which=which[score>best[which]]
 if not len(which):continue
 pts=verts[faces[which]].reshape(-1,3);q=cv2.projectPoints(pts,rv,T,K,D)[0].reshape(-1,3,2);q[:,:,0]/=1600;q[:,:,1]=1-q[:,:,1]/900;uv[which]=q;mats[which]=mi;best[which]=f/pc[which,2]
np.savez_compressed(root/'ground_context.npz',xyz=verts.astype(np.float32),faces=faces,uv=uv,material_ids=mats);(root/'ground_context.json').write_text(json.dumps(dict(source_times=times,vertices=len(verts),triangles=len(faces),textured_triangles=int((mats>0).sum()),status='Estimated ground interpolation and visibility-filtered source projection; context only, not surveyed geometry'),indent=2));print('GROUND',len(verts),len(faces),int((mats>0).sum()))
