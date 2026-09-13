"""Rectify source-visible pilot walls with final cameras and dense occlusion tests."""
import json,numpy as np,cv2,os
from pathlib import Path
from scipy import ndimage as nd
from rebuild_v4_arch_geometry import *
P=OUT/os.getenv('V4_FACADE_OUT','facades');P.mkdir(exist_ok=True);d=json.loads((OUT/os.getenv('V4_GEOMETRY','pilot_mesh_input.json')).read_text());surface=np.load(OUT/'surface_points.npz');points=surface['xyz'][::3];pw=world(points);depthcache={};imagecache={};NATIVE=OUT/'source_native';NATIVE.mkdir(exist_ok=True);DEPTH=OUT/'facade_depth';DEPTH.mkdir(exist_ok=True);metas={m['file']:m for m in json.loads((ROOT/'sfm/frames.json').read_text())};cap=None

def depth(name):
 if name in depthcache:return depthcache[name]
 path=DEPTH/(name+'.npy')
 if path.exists():
  buf=np.load(path);depthcache[name]=buf;return buf
 im,cam=camera(name);q=pw@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation;uv=cam.img_from_cam(q);ij=np.round(np.nan_to_num(uv,nan=-1e6)*.5).astype(int);z=q[:,2]*S;ok=(z>0)&(ij[:,0]>=0)&(ij[:,0]<1200)&(ij[:,1]>=0)&(ij[:,1]<675);buf=np.full((675,1200),np.inf,np.float32);np.minimum.at(buf,(ij[ok,1],ij[ok,0]),z[ok]);valid=np.isfinite(buf)
 if not valid.all():
  dist,idx=nd.distance_transform_edt(~valid,return_indices=True);near=buf[tuple(idx)];buf[dist<3]=near[dist<3]
 depthcache[name]=buf;np.save(path,buf);return buf

def source(name):
 global cap
 if name in imagecache:return imagecache[name]
 path=NATIVE/name
 if not path.exists():
  if cap is None:cap=cv2.VideoCapture('/Users/zenghang/Desktop/dji_fly_20260216_134446_0050_1771258754211_video.mp4')
  cap.set(cv2.CAP_PROP_POS_FRAMES,metas[name]['source_frame']);ok,img=cap.read();assert ok;cv2.imwrite(str(path),img,[cv2.IMWRITE_JPEG_QUALITY,98])
 img=cv2.imread(str(path));imagecache[name]=img
 if len(imagecache)>12:del imagecache[next(iter(imagecache))]
 return img

def visibility(q,name):
 im,cam=camera(name);cp=world(q)@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation;uv=cam.img_from_cam(cp);good=np.isfinite(uv).all(1)&(cp[:,2]>0);ij=np.round(np.nan_to_num(uv,nan=-1e6)*.5).astype(int);good&=(ij[:,0]>=0)&(ij[:,0]<1200)&(ij[:,1]>=0)&(ij[:,1]<675);vis=np.zeros(len(q),bool);buf=depth(name);vis[good]=cp[good,2]*S<buf[ij[good,1],ij[good,0]]+1.1;return uv,vis

entries=[];selection=set(filter(None,os.getenv('FACADE_IDS',','.join(b['id'] for b in d['entries'])).split(',')));oldpath=P/'manifest.json';old=json.loads(oldpath.read_text())['entries'] if oldpath.exists() and os.getenv('V4_RESUME','0')=='1' else [];completed={f'{e["building_id"]}_f{e["face"]:02}':e for e in old}
for b in d['entries']:
 if b['id'] not in selection:continue
 xy=np.array(b['footprint_world']);signed=np.sum(xy[:,0]*np.roll(xy[:,1],-1)-np.roll(xy[:,0],-1)*xy[:,1]);direction=1 if signed>0 else -1;ztop=b['roof_edge_height']-(.34 if b['roof_type']=='flat' else .05);zbase=b['base_height'];height=ztop-zbase
 for face,(aa,bb) in enumerate(zip(xy,np.roll(xy,-1,axis=0))):
  key=f'{b["id"]}_f{face:02}'
  if key in completed:entries.append(completed[key]);continue
  u=bb-aa;length=np.linalg.norm(u);u/=length;normal=np.r_[u[1],-u[0],0]*direction;center=np.r_[(aa+bb)/2,(ztop+zbase)/2];corners=np.array([[*aa,zbase],[*bb,zbase],[*bb,ztop],[*aa,ztop]]);samp=np.array([np.r_[aa+(bb-aa)*s,zbase+height*t] for t in np.linspace(.06,.94,11) for s in np.linspace(.04,.96,11)]);candidates=[]
  if length<1.25:continue
  for name,im in IMS.items():
   sec=float(name[6:-4])
   if not (0<=sec<=148 or 212<=sec<=269):continue
   ray=local(im.projection_center())-center;cos=normal@ray/np.linalg.norm(ray)
   if cos<.05:continue
   uv=project(corners,name)
   if not np.isfinite(uv).all():continue
   uv0=np.maximum(uv.min(0),[0,0]);uv1=np.minimum(uv.max(0),[2400,1350]);area=max(0,uv1[0]-uv0[0])*max(0,uv1[1]-uv0[1]);full=np.prod(np.maximum(uv.max(0)-uv.min(0),1));frac=area/full
   if area<500 or frac<.35:continue
   candidates.append((area*cos,cos,name))
  candidates.sort(reverse=True);best=[]
  for score,cos,name in candidates[:8]:
   uv,vis=visibility(samp,name);ratio=float(vis.mean());best.append((score*ratio**2,ratio,name,cos))
  best.sort(reverse=True)
  if not best:continue
  score,visfrac,name,cos=best[0];pp=35;nx=max(48,min(1600,round(length*pp)));ny=max(64,min(1400,round(height*pp)));ss=np.linspace(0,1,nx);tt=np.linspace(1,0,ny);gx,gy=np.meshgrid(ss,tt);q=np.column_stack([(aa[0]+(bb[0]-aa[0])*gx).ravel(),(aa[1]+(bb[1]-aa[1])*gx).ravel(),(zbase+height*gy).ravel()]);uv,vis=visibility(q,name);img=source(name);factor=img.shape[1]/2400;maps=(uv*factor).reshape((ny,nx,2)).astype(np.float32);rect=cv2.remap(img,maps[...,0],maps[...,1],cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=(220,220,220));mask=vis.reshape(ny,nx);prefix=f'{b["id"]}_f{face:02}';cv2.imwrite(str(P/(prefix+'.jpg')),rect,[cv2.IMWRITE_JPEG_QUALITY,95]);cv2.imwrite(str(P/(prefix+'_visible.png')),mask.astype(np.uint8)*255);preview=rect.copy();preview[~mask]=(preview[~mask]*.25+np.array([45,45,110])*.75).astype(np.uint8);cv2.imwrite(str(P/(prefix+'_review.jpg')),preview)
  ent=dict(building_id=b['id'],face=face,image=name,source_frame=metas[name]['source_frame'],length=length,height=height,zbase=zbase,ztop=ztop,start=aa.tolist(),end=bb.tolist(),outward=normal.tolist(),pixels_per_unit=pp,rectified_width=nx,rectified_height=ny,visible_fraction=visfrac,camera_cos=cos,candidates=[dict(image=n,visible_fraction=v,score=s) for s,v,n,c in best],status='source rectification with approximate dense occlusion; openings not yet annotated');entries.append(ent);print(prefix,name,'visible',round(visfrac,2),'size',nx,ny,flush=True)
  if len(entries)%30==0:(P/'manifest.json').write_text(json.dumps(dict(entries=entries),indent=2))
(P/'manifest.json').write_text(json.dumps(dict(entries=entries),indent=2))
if cap is not None:cap.release()
print('RECTIFICATION_DONE',len(entries),flush=True)
