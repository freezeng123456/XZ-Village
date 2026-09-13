"""Attach visually normalized real feature matches to both local frame tracks."""
import json,sqlite3,itertools,time,os
from pathlib import Path
import numpy as np,cv2,pycolmap as pc
from scipy.spatial import cKDTree
root=Path('work/rebuild4');unified=os.environ.get('UNIFIED','0')=='1';base=[int(os.environ.get('PAIR_A','44')),int(os.environ.get('PAIR_B','256'))];suffix=f'_{base[0]:03d}_{base[1]:03d}' if unified else '';out=root/('bridge'+suffix);out.mkdir(exist_ok=True);start=time.time()
pairpath=root/('plane_guided_learned'+suffix)/'calibrated_matches.npz';data=np.load(pairpath);ids=data['matches'];points=[data['p'][ids[:,0]],data['q'][ids[:,1]]];N=len(ids)
recs=[pc.Reconstruction(root/('sfm/sparse_unified/0' if unified else 'sfm/sparse_bounded/1')),pc.Reconstruction(root/('sfm/sparse_unified/0' if unified else 'sfm/sparse_bounded/0'))]
times=[[36,38,40,42,44,46,48,50,52],[244,246,248,250,252,254,255,256,257,258,260,262,264]]
if unified:times=[sorted(int(float(im.name[6:-4])) for im in recs[f].images.values() if im.has_pose and abs(float(im.name[6:-4])-base[f])<=(10 if f==0 else 12)) for f in [0,1]]
cache={};tracks={};quality={}
def photo(t):
 name=f'frame_{t:06.2f}.jpg'
 if name not in cache:cache[name]=cv2.imread(str(root/'sfm/images'/name),cv2.IMREAD_GRAYSCALE)
 return cache[name]
def camera(f,t):
 im=recs[f].find_image_with_name(f'frame_{t:06.2f}.jpg');return im,recs[f].cameras[im.camera_id]
for f in [0,1]:
 im0,c0=camera(f,base[f]);p0=points[f].astype(np.float32);xy=[];zz=[]
 for pt in im0.points2D:
  if pt.has_point3D():xy.append(pt.xy);zz.append((im0.cam_from_world()*recs[f].points3D[pt.point3D_id].xyz)[2])
 _,ix=cKDTree(xy).query(p0,k=3);depth=np.median(np.array(zz)[ix],axis=1);rays=np.c_[c0.cam_from_img(p0.astype(float)),np.ones(N)];X=(depth[:,None]*rays-im0.cam_from_world().translation)@im0.cam_from_world().rotation.matrix()
 for tm in times[f]:
  im,c=camera(f,tm)
  if tm==base[f]:tracks[im.image_id]={i:p0[i].tolist() for i in range(N)};quality[str(im.image_id)]=dict(time=tm,flight=f,accepted=N,reference=True);continue
  v=X@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation;pred=c.img_from_cam(v);pred=np.nan_to_num(pred,nan=-1e5,posinf=1e5,neginf=-1e5).astype(np.float32)
  valid=np.all(p0>[13,13],axis=1)&np.all(p0<[2387,1337],axis=1)&(v[:,2]>0)&np.all(pred>[-50,-50],axis=1)&np.all(pred<[2450,1400],axis=1);use=np.flatnonzero(valid)
  if len(use)==0:continue
  best={};rel=im.cam_from_world()*im0.cam_from_world().inverse();u=np.c_[c0.cam_from_img(p0[use].astype(float)),np.ones(len(use))];lines=np.cross(rel.translation,(u@rel.rotation.matrix().T))
  for win in [15,25,41]:
   old=p0[use].reshape(-1,1,2);init=pred[use].reshape(-1,1,2).copy();new,st,err=cv2.calcOpticalFlowPyrLK(photo(base[f]),photo(tm),old,init,winSize=(win,win),maxLevel=5,flags=cv2.OPTFLOW_USE_INITIAL_FLOW,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.001))
   rev,st2,_=cv2.calcOpticalFlowPyrLK(photo(tm),photo(base[f]),new,old.copy(),winSize=(win,win),maxLevel=5,flags=cv2.OPTFLOW_USE_INITIAL_FLOW,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.001))
   fb=np.linalg.norm(rev-old,axis=(1,2));q=new[:,0];vv=np.c_[c.cam_from_img(q.astype(float)),np.ones(len(q))];epi=np.abs(np.sum(vv*lines,axis=1))/np.maximum(1e-12,np.linalg.norm(lines[:,:2],axis=1))*c.focal_length
   ok=st[:,0].astype(bool)&st2[:,0].astype(bool)&(fb<1.2)&(err[:,0]<32)&(epi<2.5)&np.all(q>[6,6],axis=1)&np.all(q<[2394,1344],axis=1)&(np.linalg.norm(q-pred[use],axis=1)<80)
   for j in np.flatnonzero(ok):
    score=float(err[j,0]+20*fb[j]);fid=int(use[j])
    if fid not in best or score<best[fid][0]:best[fid]=(score,q[j].tolist())
  tracks[im.image_id]={i:v[1] for i,v in best.items()};quality[str(im.image_id)]=dict(time=tm,flight=f,accepted=len(best),reference=False);print('TRACK',f,tm,len(best),flush=True)
counts=np.zeros((2,N),int)
for iid,tr in tracks.items():
 f=quality[str(iid)]['flight']
 for fid in tr:counts[f,fid]+=1
keep=np.flatnonzero((counts[0]>=3)&(counts[1]>=3));keep_set=set(keep.tolist());print('KEPT_TRACKS',len(keep),flush=True)
for iid in tracks:tracks[iid]={fid:xy for fid,xy in tracks[iid].items() if fid in keep_set}
(out/'observations.json').write_text(json.dumps(dict(source_pairs=str(pairpath),time0=base[0],time1=base[1],input_pairs=N,retained_features=len(keep),observations={str(k):v for k,v in tracks.items()},image_quality=quality),indent=2))
if len(keep)<30:raise RuntimeError('Too few supported cross-flight image tracks')
target=root/'sfm'/os.environ.get('TARGET_DB','bridge.db')
if target.exists():raise RuntimeError('Refusing to overwrite an existing bridge database')
source=sqlite3.connect(root/'sfm'/os.environ.get('SOURCE_DB','bounded.db'));db=sqlite3.connect(target);source.backup(db);source.close();new_indices={}
for iid,tr in tracks.items():
 n,cols,b=db.execute('SELECT rows,cols,data FROM keypoints WHERE image_id=?',(iid,)).fetchone();kp=np.frombuffer(b,np.float32).reshape(n,cols);new=np.zeros((len(tr),cols),np.float32);new[:,2]=1
 if cols==6:new[:,5]=1
 ni={}
 for j,(fid,xy) in enumerate(tr.items()):new[j,:2]=xy;ni[fid]=n+j
 new_indices[iid]=ni;full=np.vstack([kp,new]);db.execute('UPDATE keypoints SET rows=?,data=? WHERE image_id=?',(len(full),full.tobytes(),iid))
 n,cols,b=db.execute('SELECT rows,cols,data FROM descriptors WHERE image_id=?',(iid,)).fetchone();desc=np.frombuffer(b,np.uint8).reshape(n,cols);desc=np.vstack([desc,np.zeros((len(tr),cols),np.uint8)]);db.execute('UPDATE descriptors SET rows=?,data=? WHERE image_id=?',(len(desc),desc.tobytes(),iid))
# Existing learned/tracked points have no SIFT descriptor; no descriptor matcher
# may be run on this augmented database. Mapping consumes the verified tracks.
params=np.mean([recs[0].cameras[1].params,recs[1].cameras[1].params],axis=0);db.execute('UPDATE cameras SET params=? WHERE camera_id=1',(params.astype(np.float64).tobytes(),));pairs=[]
for a,b in itertools.combinations(sorted(new_indices),2):
 shared=sorted(set(new_indices[a])&set(new_indices[b]));extra=np.array([[new_indices[a][i],new_indices[b][i]] for i in shared],np.uint32).reshape(-1,2)
 if len(extra)<15:continue
 pid=a*2147483647+b;row=db.execute('SELECT rows,cols,data FROM matches WHERE pair_id=?',(pid,)).fetchone();old=np.frombuffer(row[2],np.uint32).reshape(row[0],2) if row and row[0]>0 and row[2] is not None else np.zeros((0,2),np.uint32);matches=np.unique(np.vstack([old,extra]),axis=0)
 db.execute('INSERT OR REPLACE INTO matches(pair_id,rows,cols,data) VALUES(?,?,?,?)',(pid,len(matches),2,matches.tobytes()));pairs.append((a,b,len(extra)))
db.commit();db.close();pdb=pc.Database.open(target);cam=pdb.read_camera(1)
opts=pc.TwoViewGeometryOptions(dict(compute_relative_pose=True,ransac=dict(max_error=3,min_inlier_ratio=.1,max_num_trials=20000,random_seed=916)))
verification=[]
for a,b,n in pairs:
 kp0=pdb.read_keypoints(a);kp1=pdb.read_keypoints(b);mt=pdb.read_matches(a,b);geom=pc.estimate_calibrated_two_view_geometry(cam,np.ascontiguousarray(kp0[:,:2],dtype=np.float64),cam,np.ascontiguousarray(kp1[:,:2],dtype=np.float64),mt,opts)
 if pdb.exists_two_view_geometry(a,b):pdb.update_two_view_geometry(a,b,geom)
 else:pdb.write_two_view_geometry(a,b,geom)
 cross=quality[str(a)]['flight']!=quality[str(b)]['flight'];verification.append(dict(a=a,b=b,new_matches=n,inliers=len(geom.inlier_matches),cross_flight=cross,configuration=int(geom.config)))
pdb.close();summary=dict(retained_cross_flight_features=len(keep),images=len(tracks),added_observations=sum(len(v) for v in tracks.values()),verified_cross_pairs=sum(r['cross_flight'] and r['inliers']>=15 for r in verification),pairs=verification,elapsed_seconds=time.time()-start,descriptor_matching_forbidden_on_augmented_database=True)
(out/'database_summary.json').write_text(json.dumps(summary,indent=2));print('BRIDGE_READY',summary['retained_cross_flight_features'],summary['verified_cross_pairs'],summary['elapsed_seconds'],flush=True)
