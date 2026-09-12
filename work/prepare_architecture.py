"""Source-traced architectural candidates. No automatic acceptance of openings."""
from pathlib import Path
import json,cv2,numpy as np,pycolmap
from aerial_common import load_main
root=Path('work/aerial');out=Path('work/buildings');(out/'facades').mkdir(exist_ok=True)
a=json.loads((root/'alignment.json').read_text());R=np.array(a['rotation']);T=np.array(a['translation']);S=a['scale'];rec=load_main(root/'sfm');ann=json.loads((out/'roof_annotations.json').read_text());result=[];cached={}
for b in ann['buildings']:
 if b.get('duplicate_of'):continue
 ts=b['t']
 if ts not in cached:
  if ts==256:
   rr=pycolmap.Reconstruction(root/'sfm/sparse/2');im=next(i for i in rr.images.values() if i.name=='f256.00.jpg');cam=rr.cameras[im.camera_id];ca=json.loads((out/'return_camera_roof_candidate.json').read_text());C=np.array(ca['position']);cr=np.array(ca['rotation_world_to_camera']);ct=np.array(ca['translation_world_to_camera']);xyz=np.empty((0,3));uv=np.empty((0,2));LR=np.eye(3);LT=np.zeros(3);LS=1
  else:
   im=next(i for i in rec.images.values() if i.name==f'f{ts:06.2f}.jpg');cam=rec.cameras[im.camera_id];C=S*R@im.projection_center()+T;cr=im.cam_from_world().rotation.matrix();ct=im.cam_from_world().translation;LR=R;LT=T;LS=S
   fp=root/f'sfm/flow/f{ts:06.2f}__f{ts+2:06.2f}.npz'
   if fp.exists():z=np.load(fp);xyz=z['xyz']@R.T*S+T;uv=z['uv']
   else:xyz=np.empty((0,3));uv=np.empty((0,2))
  src=cv2.imread(str(root/f'sfm/images/{im.name}'));cached[ts]=(im,cam,C,cr,ct,xyz,uv,src,LR,LT,LS)
 im,cam,C,cr,ct,xyz,uv,src,LR,LT,LS=cached[ts]
 poly=np.array(b['roof'],np.float32);inside=np.array([cv2.pointPolygonTest(poly,tuple(p),True)>1.8 for p in uv],bool);support=xyz[inside];height=b['floors']*3.3
 if len(support)>8:
  values,counts=np.unique(np.round(support[:,2]/.3),return_counts=True);mode=values[np.argmax(counts)]*.3;inliers=np.abs(support[:,2]-mode)<.5;height=float(np.median(support[inliers,2]));std=float(np.std(support[inliers,2]));num=int(inliers.sum())
 else:
  sparse=np.array([rec.points3D[p.point3D_id].xyz@R.T*S+T for p in im.points2D if p.has_point3D() and cv2.pointPolygonTest(poly,tuple(p.xy),True)>1]) if ts!=256 else []
  if len(sparse):height=float(np.median(sparse[:,2]));std=float(np.std(sparse[:,2]));num=len(sparse)
  else:std=None;num=0
 if 'height_override' in b:height=b['height_override']
 if not 2.4<height<20:height=b['floors']*3.3;num=0
 rays=np.column_stack((cam.cam_from_img(poly.astype(float)),np.ones(len(poly))))@cr@LR.T;verts=C+rays*((height-C[2])/rays[:,2])[:,None]
 if np.sum(verts[:,0]*np.roll(verts[:,1],-1)-verts[:,1]*np.roll(verts[:,0],-1))<0:verts=verts[::-1]
 def project(p):
  raw=(np.array(p)-LT)@LR/LS;return cam.img_from_cam(raw@cr.T+ct)
 faces=[]
 for j,(v,w) in enumerate(zip(verts,np.roll(verts,-1,axis=0))):
  d=w-v;L=np.linalg.norm(d[:2]);normal=np.array([d[1],-d[0],0])/L;visible=normal@(C-(v+w)/2)>0
  if not visible or L<1.5:continue
  width=max(64,round(L*40));h=max(100,round(height*40));dst=np.array([[0,h-1],[width-1,h-1],[width-1,0],[0,0]],np.float32);corners=np.array([[v[0],v[1],0],[w[0],w[1],0],w,v]);px=project(corners).astype(np.float32)
  hom=cv2.getPerspectiveTransform(px,dst);patch=cv2.warpPerspective(src,hom,(width,h));path=out/f'facades/{b["id"]}_{j}.jpg';cv2.imwrite(str(path),patch)
  gray=cv2.cvtColor(patch,cv2.COLOR_BGR2GRAY);valid=gray>5;threshold=min(95,np.percentile(gray[valid],23)) if valid.any() else 60;mask=np.uint8((gray<threshold)&valid)*255
  mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8));n,labels,stats,centers=cv2.connectedComponentsWithStats(mask)
  windows=[]
  for x,y,pw,ph,area in stats[1:]:
   rw=pw/width*L;rh=ph/h*height;fill=area/(pw*ph)
   if .42<rw<2.4 and .55<rh<2.5 and fill>.5 and .23<rw/rh<2.6 and x>width*.05 and x+pw<width*.95 and y>h*.07 and y+ph<h*.92:
    windows.append([float(x/width*L),float((x+pw)/width*L),float((1-(y+ph)/h)*height),float((1-y/h)*height)])
  faces.append(dict(edge=j,length=float(L),image=str(path),source_corners=px.tolist(),opening_candidates=windows,status='unreviewed automatic dark-region candidates; source occlusion may contaminate'))
 b.update(roof_world=verts.tolist(),roof_height=height,roof_support=num,roof_height_std=std,base_height=0,facades=faces,status='traced; awaiting geometry and source comparison review');result.append(b)
path=out/'architecture_candidates.json';path.write_text(json.dumps(dict(buildings=result),ensure_ascii=False,indent=2));print(json.dumps([dict(id=b['id'],height=round(b['roof_height'],2),support=b['roof_support'],openings=sum(len(f['opening_candidates']) for f in b['facades'])) for b in result],indent=2))
# Numbered source coverage sheet.
for ts in cached:
 im=cached[ts][7].copy()
 for b in result:
  if b['t']!=ts:continue
  p=np.array(b['roof'],np.int32);cv2.polylines(im,[p],True,(0,220,255),1);xy=tuple(p.mean(0).astype(int));cv2.putText(im,b['id'],xy,cv2.FONT_HERSHEY_SIMPLEX,.4,(0,0,0),3);cv2.putText(im,b['id'],xy,cv2.FONT_HERSHEY_SIMPLEX,.4,(0,240,255),1)
 cv2.imwrite(str(out/f'coverage_{ts:03}.jpg'),im)
# Review all facades at a consistent card size.
cards=[]
for b in result:
 for f in b['facades']:
  im=cv2.imread(f['image']);H,W=im.shape[:2]
  for x0,x1,z0,z1 in f['opening_candidates']:
   cv2.rectangle(im,(round(x0/f['length']*W),round((1-z1/b['roof_height'])*H)),(round(x1/f['length']*W),round((1-z0/b['roof_height'])*H)),(0,0,255),2)
  sc=min(270/W,260/H);im=cv2.resize(im,None,fx=sc,fy=sc);card=np.full((300,290,3),235,np.uint8);card[32:32+im.shape[0],:im.shape[1]]=im;cv2.putText(card,b['id']+' edge '+str(f['edge']),(8,22),cv2.FONT_HERSHEY_SIMPLEX,.6,(20,20,20),1);cards.append(card)
for page in range((len(cards)+15)//16):
 group=cards[page*16:(page+1)*16];group+= [np.full_like(cards[0],235)]*(16-len(group));sheet=np.vstack([np.hstack(group[i:i+4]) for i in range(0,16,4)]);cv2.imwrite(str(out/f'facade_candidates_{page+1}.jpg'),sheet)
