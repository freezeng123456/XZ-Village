"""Depth-tested source assignment and opening candidates, with review cards.

Only model-visible source pixels are transferred. Vegetation, unmodelled
occluders, camera error and segmentation still require visual review.
"""
from pathlib import Path
import json,cv2,numpy as np,pycolmap
from scipy.spatial import Delaunay
from aerial_common import load_main
ROOT=Path.cwd();root=ROOT/'work/aerial';out=ROOT/'work/buildings';dst=out/'visibility';dst.mkdir(exist_ok=True);(dst/'masks').mkdir(exist_ok=True);(dst/'faces').mkdir(exist_ok=True)
data=json.loads((out/'architecture_candidates.json').read_text());bs=data['buildings'];rec=load_main(root/'sfm');a=json.loads((root/'alignment.json').read_text());AR=np.array(a['rotation']);AT=np.array(a['translation']);AS=a['scale'];poses={};buffers={};frames={}
def raster(uv,z,label,depth,ids,fid):
 if not np.isfinite(uv).all() or min(z)<.1:return
 x0=max(0,int(np.floor(uv[:,0].min())));x1=min(1599,int(np.ceil(uv[:,0].max())));y0=max(0,int(np.floor(uv[:,1].min())));y1=min(899,int(np.ceil(uv[:,1].max())))
 if x1<x0 or y1<y0:return
 yy,xx=np.mgrid[y0:y1+1,x0:x1+1];p0,p1,p2=uv;den=(p1[1]-p2[1])*(p0[0]-p2[0])+(p2[0]-p1[0])*(p0[1]-p2[1])
 if abs(den)<.01:return
 aa=((p1[1]-p2[1])*(xx-p2[0])+(p2[0]-p1[0])*(yy-p2[1]))/den;bb=((p2[1]-p0[1])*(xx-p2[0])+(p0[0]-p2[0])*(yy-p2[1]))/den;cc=1-aa-bb;inside=(aa>=0)&(bb>=0)&(cc>=0);iz=aa/z[0]+bb/z[1]+cc/z[2];zz=1/np.maximum(iz,1e-9);view=depth[y0:y1+1,x0:x1+1];take=inside&(zz<view);view[take]=zz[take];ids[y0:y1+1,x0:x1+1][take]=fid
for ts in sorted(set([0,20,44,60,76,104,256]+[b['t'] for b in bs])):
 if ts==256:
  c=json.loads((out/'return_camera_roof_candidate.json').read_text());R=np.array(c['rotation_world_to_camera']);T=np.array(c['translation_world_to_camera']);C=np.array(c['position']);f=c['K'][0][0];k=c['distortion'][0]
 else:
  im=next(i for i in rec.images.values() if i.name==f'f{ts:06.2f}.jpg');cam=rec.cameras[im.camera_id];R=im.cam_from_world().rotation.matrix()@AR.T;C=AS*AR@im.projection_center()+AT;T=-R@C;f,k=cam.params[0],cam.params[3]
 K=np.array([[f,0,800],[0,f,450],[0,0,1]],float);D=np.array([k,0,0,0,0]);rv=cv2.Rodrigues(R)[0]
 def project(q):return cv2.projectPoints(np.array(q,float),rv,T,K,D)[0].reshape(-1,2)
 depth=np.full((900,1600),np.inf,np.float32);ids=np.zeros((900,1600),np.uint16)
 for bi,b in enumerate(bs):
  p=np.array(b['roof_world']);n=len(p);bottom=p.copy();bottom[:,2]=b.get('base_height',0);world=np.vstack([bottom,p]);uv=project(world);z=(world@R.T+T)[:,2]
  for j in range(n):
   idx=[j,(j+1)%n,(j+1)%n+n,j+n]
   for tri in [[idx[0],idx[1],idx[2]],[idx[0],idx[2],idx[3]]]:raster(uv[tri],z[tri],0,depth,ids,(bi+1)*16+j)
  # OpenCV triangulates the projected roof polygon including concave outlines.
  for tri0 in Delaunay(p[:,:2]).simplices:
   triangle=p[tri0,:2];checks=np.vstack([triangle.mean(0),(triangle+np.roll(triangle,-1,axis=0))/2]);poly=p[:,:2].astype(np.float32)
   if any(cv2.pointPolygonTest(poly,tuple(q),True)<-.001 for q in checks):continue
   tri=tri0+n;raster(uv[tri],z[tri],0,depth,ids,(bi+1)*16+15)
 srcpath=out/f'source_{ts}_4k.jpg'
 if not srcpath.exists():srcpath=root/f'sfm/images/f{ts:06.2f}.jpg'
 src=cv2.imread(str(srcpath));frames[ts]=src;buffers[ts]=ids;poses[ts]=dict(rotation=R.tolist(),translation=T.tolist(),position=C.tolist(),focal=float(f),radial=float(k),source=str(srcpath.relative_to(ROOT)),source_width=src.shape[1],source_height=src.shape[0]);cv2.imwrite(str(dst/f'face_ids_{ts:03}.png'),ids);print('RASTER',ts,int((ids>0).sum()),flush=True)
cards=[];total=0
def save_mask(mask,path):
 points=cv2.findNonZero(mask)
 if points is None:x,y,w,h=0,0,1,1
 else:x,y,w,h=cv2.boundingRect(points)
 cv2.imwrite(str(path),mask[y:y+h,x:x+w]);return [x,y,w,h]
for bi,b in enumerate(bs):
 p=np.array(b['roof_world']);base=b.get('base_height',0);h=b['roof_height']-base;b['visible_facades']=[]
 ts=b['t'];roofmask=np.uint8(buffers[ts]==(bi+1)*16+15)*255;rp=dst/f'masks/{b["id"]}_roof.png';bounds=save_mask(roofmask,rp);small=cv2.resize(frames[ts],(1600,900),interpolation=cv2.INTER_AREA);pix=small[roofmask>0]
 b['roof_texture']=dict(source_time=ts,mask=str(rp.relative_to(ROOT)),mask_bounds_px=bounds,visible_pixels=len(pix),rgb=(np.median(pix[:,::-1],axis=0)/255).tolist() if len(pix) else [.5,.45,.38])
 for j,(v,w) in enumerate(zip(p,np.roll(p,-1,axis=0))):
  fid=(bi+1)*16+j;best=max(buffers,key=lambda ts:int(np.sum(buffers[ts]==fid)));pixelcount=int(np.sum(buffers[best]==fid))
  if pixelcount<25:continue
  pose=poses[best];R=np.array(pose['rotation']);T=np.array(pose['translation']);K=np.array([[pose['focal'],0,800],[0,pose['focal'],450],[0,0,1]],float);D=np.array([pose['radial'],0,0,0,0]);rv=cv2.Rodrigues(R)[0];L=np.linalg.norm(w-v);W=max(40,round(L*40));H=max(80,round(h*40));corners=np.array([[v[0],v[1],base],[w[0],w[1],base],w,v]);uv=cv2.projectPoints(corners,rv,T,K,D)[0].reshape(-1,2).astype(np.float32);target=np.array([[0,H-1],[W-1,H-1],[W-1,0],[0,0]],np.float32)
  hom=cv2.getPerspectiveTransform(uv,target);mask=np.uint8(buffers[best]==fid)*255;vm=cv2.warpPerspective(mask,hom,(W,H),flags=cv2.INTER_NEAREST);vm=cv2.erode(vm,np.ones((3,3),np.uint8));src=frames[best];scale=src.shape[1]/1600;srcH=cv2.getPerspectiveTransform(uv*scale,target);patch=cv2.warpPerspective(src,srcH,(W,H));gray=cv2.cvtColor(patch,cv2.COLOR_BGR2GRAY);valid=vm>0
  if valid.sum()<40:continue
  th=min(115,float(np.median(gray[valid]))*.63);dark=(gray<th)&(gray>6)&valid;bw=np.uint8(dark)*255;bw=cv2.morphologyEx(bw,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));n,labels,stats,cent=cv2.connectedComponentsWithStats(bw);holes=[]
  for x,y,pw,ph,area in stats[1:]:
   ww=pw/W*L;hh=ph/H*h;fill=area/(pw*ph)
   if .35<ww<3.4 and .45<hh<2.8 and .25<ww/hh<3.4 and fill>.48 and x>W*.035 and x+pw<W*.965 and y>H*.06 and y+ph<H*.98 and np.mean(valid[y:y+ph,x:x+pw])>.92:
    holes.append([float(x/W*L),float((x+pw)/W*L),float((1-(y+ph)/H)*h),float((1-y/H)*h)])
  maskpath=dst/f'masks/{b["id"]}_edge{j}.png';bounds=save_mask(mask,maskpath);patchpath=dst/f'faces/{b["id"]}_edge{j}.jpg';cv2.imwrite(str(patchpath),patch)
  item=dict(edge=j,source_time=best,source_visible_pixels=pixelcount,mask=str(maskpath.relative_to(ROOT)),mask_bounds_px=bounds,patch=str(patchpath.relative_to(ROOT)),opening_candidates=holes,source_corners=uv.tolist(),status='Depth-tested source and automatic opening candidates; not individual visual acceptance');b['visible_facades'].append(item);total+=len(holes)
  review=patch.copy();review[~valid]=(review[~valid]*.15+190).astype(np.uint8)
  for x0,x1,z0,z1 in holes:cv2.rectangle(review,(round(x0/L*W),round((1-z1/h)*H)),(round(x1/L*W),round((1-z0/h)*H)),(0,0,255),2)
  sc=min(220/W,230/H);review=cv2.resize(review,None,fx=sc,fy=sc);card=np.full((270,240,3),238,np.uint8);card[30:30+review.shape[0],:review.shape[1]]=review;cv2.putText(card,f'{b["id"]} e{j} / {best}s',(5,21),cv2.FONT_HERSHEY_SIMPLEX,.48,(20,20,20),1);cards.append(card)
 (dst/'architecture_visibility.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(dst/'poses.json').write_text(json.dumps(poses,indent=2));print('OPENING_CANDIDATES',total,'FACADES',len(cards),flush=True)
for page in range((len(cards)+24)//25):
 group=cards[page*25:(page+1)*25];group+=[np.full_like(cards[0],238)]*(25-len(group));sheet=np.vstack([np.hstack(group[i:i+5]) for i in range(0,25,5)]);cv2.imwrite(str(dst/f'review_{page+1:02}.jpg'),sheet)
