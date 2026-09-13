"""Camera-fixed multi-view plane sweep for texture-poor or incomplete roof support.
Proposes roof heights from actual neighboring image intensities, with ambiguity recorded.
"""
import json,cv2,numpy as np,os
from pathlib import Path
from rebuild_v4_arch_geometry import *
P=OUT;cache={}
def gray(name):
 if name not in cache:
  im=cv2.imread(str(ROOT/'sfm/images'/name));g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32);g=cv2.GaussianBlur(g,(3,3),.65);cache[name]=g
 return cache[name]
def solve(name,mask,base,zprior=None):
 image=gray(name);er=cv2.erode(mask,np.ones((3,3),np.uint8));yy,xx=np.where(er>0);points=np.column_stack([xx,yy]);gx=cv2.Sobel(image,cv2.CV_32F,1,0);gy=cv2.Sobel(image,cv2.CV_32F,0,1);grad=np.hypot(gx[yy,xx],gy[yy,xx]);keep=grad>max(8,np.percentile(grad,45));points=points[keep];
 if len(points)<30:return dict(status='insufficient source texture',points=len(points))
 rng=np.random.default_rng(124);points=points[rng.choice(len(points),min(900,len(points)),replace=False)].astype(float);ref=cv2.remap(image,points[:,0].astype(np.float32)[:,None],points[:,1].astype(np.float32)[:,None],cv2.INTER_LINEAR).ravel();C,dr=rays(points,name);sec=float(name[6:-4]);neighbors=[]
 for nn,im in IMS.items():
  delta=abs(float(nn[6:-4])-sec);baseline=np.linalg.norm(local(im.projection_center())-C)
  if 1.4<=delta<=8 and 5<baseline<85:neighbors.append((abs(delta-5.0),nn,baseline))
 neighbors.sort();chosen=[];side_counts={-1:0,1:0}
 for _,nn,bl in neighbors:
  if len(chosen)>=6:break
  side=1 if float(nn[6:-4])>sec else -1
  if side_counts[side]>=3 and any((1 if float(v[1][6:-4])>sec else -1)!=side for v in neighbors):continue
  chosen.append(nn);side_counts[side]+=1
 if not chosen:return dict(status='no neighboring views',points=len(points))
 zrange=np.arange(base+1.0,base+24.0,.15) if zprior is None else np.arange(max(base+.8,zprior-3.0),zprior+3.0,.1)
 xyz=C[None,None,:]+dr[None,:,:]*((zrange[:,None]-C[2])/dr[None,:,2])[:,:,None];xx=xyz.reshape(-1,3);scores=[];perview=[]
 for nn in chosen:
  uv=project(xx,nn).reshape(len(zrange),len(points),2);valid=(uv[:,:,0]>=1)&(uv[:,:,0]<2398)&(uv[:,:,1]>=1)&(uv[:,:,1]<1348);target=cv2.remap(gray(nn),uv[:,:,0].astype(np.float32),uv[:,:,1].astype(np.float32),cv2.INTER_LINEAR);score=[]
  for k,tar in enumerate(target):
   ok=valid[k];r=ref[ok];t=tar[ok]
   if ok.mean()<.35 or len(r)<25 or np.std(t)<3 or np.std(r)<3:score.append(-1.);continue
   # Exposure offset and gain do not determine geometry.
   r=(r-np.mean(r))/max(5,np.std(r));t=(t-np.mean(t))/max(5,np.std(t));err=(r-t)**2;cut=np.percentile(err,85);sel=err<cut;score.append(float(1-np.mean(err[sel])/2))
  perview.append(score)
 combined=np.mean(np.sort(perview,axis=0)[-min(2,len(perview)):],axis=0);best=int(np.argmax(combined));top=float(combined[best]);z=float(zrange[best]);away=abs(zrange-z)>1;prom=float(top-np.max(combined[away])) if away.any() else 0
 return dict(status='height proposal',z=z,score=top,prominence_over_1unit=prom,source_samples=len(points),neighbors=chosen,grid_z=zrange.tolist(),scores=combined.tolist(),prior=zprior)
if __name__=='__main__':
 entries=json.loads((P/'pilot_mesh_input.json').read_text())['entries'];results=[]
 for b in entries:
  if b['id'] not in ['P001','P002','P005','P011','P003W1']:continue
  poly=np.array(b['roof_polygon_px']);mask=np.zeros((1350,2400),np.uint8);cv2.fillPoly(mask,[poly],255);r=solve('frame_044.00.jpg',mask,b['base_height'],b['observed_roof_surface_height']);r['id']=b['id'];r['reference_roof_surface']=b['observed_roof_surface_height'];results.append(r);print(b['id'],r['status'],round(r.get('z',0),2),'REF',b['observed_roof_surface_height'],'SCORE',r.get('score'),'PROM',r.get('prominence_over_1unit'),flush=True)
 (P/'photometric_pilot_trial.json').write_text(json.dumps(results,indent=2))
