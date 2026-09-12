"""Constrain all building cores to true rectangles while fitting observed roof projections."""
from pathlib import Path
import json,numpy as np,cv2
from scipy.optimize import least_squares
root=Path.cwd();out=root/'work/buildings/v2';out.mkdir(exist_ok=True);data=json.loads((root/'work/buildings/visibility/architecture_visibility.json').read_text());poses=json.loads((root/'work/buildings/visibility/poses.json').read_text());audit=[]
def project(xyz,pose):
 p=np.array(xyz)@np.array(pose['rotation']).T+pose['translation'];xy=p[:,:2]/p[:,2,None];return xy*(1+pose['radial']*(xy*xy).sum(1))[:,None]*pose['focal']+[800,450]
def rectangle(x,z):
 cx,cy,lw,ld,theta=x;u=np.array([np.cos(theta),np.sin(theta)]);v=np.array([-u[1],u[0]]);return np.column_stack((np.array([cx,cy])+np.array([[-1,-1],[1,-1],[1,1],[-1,1]])@np.diag(np.exp([lw,ld]))@np.array([u,v])/2,np.full(4,z)))
def sample(poly,n=8):return np.vstack([a+(b-a)*np.linspace(0,1,n,endpoint=False)[:,None] for a,b in zip(poly,np.roll(poly,-1,axis=0))])
def distances(points,poly):
 a=poly;b=np.roll(poly,-1,axis=0);e=b-a;t=np.clip(((points[:,None,:]-a)*e).sum(2)/(e*e).sum(1),0,1);return np.sqrt(np.min(((points[:,None,:]-a-t[:,:,None]*e)**2).sum(2),axis=1)+1e-8)
def iou(a,b):
 allp=np.vstack([a,b]);lo=allp.min(0)-3;hi=allp.max(0)+3;scale=min(5,800/max(hi-lo));size=np.maximum(8,np.ceil((hi-lo)*scale).astype(int));m=[]
 for p in [a,b]:
  im=np.zeros((size[1],size[0]),np.uint8);cv2.fillPoly(im,[np.round((p-lo)*scale).astype(np.int32)],1);m.append(im)
 return float((m[0]&m[1]).sum()/max(1,(m[0]|m[1]).sum()))
for b in data['buildings']:
 q=np.array(b['roof_world']);z=float(b['roof_height']);pose=poses[str(b['t'])];edge=q[1,:2]-q[0,:2];theta=np.arctan2(edge[1],edge[0]);u=np.array([np.cos(theta),np.sin(theta)]);v=np.array([-u[1],u[0]]);uv=q[:,:2]@np.array([u,v]).T;lo=uv.min(0);hi=uv.max(0);center=(lo+hi)/2@np.array([u,v]);wd=np.maximum(hi-lo,1.2);x0=np.r_[center,np.log(wd),theta];projected_old=project(q,pose);target=np.array(b['roof'],float)
 if len(target)==4:
  choices=[np.roll(t,k,axis=0) for t in [target,target[::-1]] for k in range(4)];target=min(choices,key=lambda t:np.square(t-(projected_old if len(q)==4 else project(rectangle(x0,z),pose))).sum())
 span=max(np.ptp(target,axis=0).max(),4)
 def residual(x):
  poly=project(rectangle(x,z),pose)
  if len(target)==4:r=(poly-target).ravel()
  else:r=np.r_[distances(sample(target),poly),distances(sample(poly),target)]
  return np.r_[r,(x[:2]-x0[:2])*.04,(x[2:4]-x0[2:4])*.5,(x[4]-theta)*.2]
 lower=x0-np.r_[wd.max(),wd.max(),.65,.65,.14 if len(q)!=4 else .25];upper=x0+np.r_[wd.max(),wd.max(),.65,.65,.14 if len(q)!=4 else .25]
 if b['id'].startswith(('F','G')):
  lower[2:4]=np.log([max(3.8,wd[0]*.75),5.2 if b['type']=='gable' else 6.4]);upper[2:4]=np.log([max(4.2,min(18,wd[0]*1.25)),8.2 if b['type']=='gable' else 10.7]);x0=np.maximum(lower+1e-6,np.minimum(upper-1e-6,x0))
 sol=least_squares(residual,x0,bounds=(lower,upper),loss='soft_l1',f_scale=max(1,span*.015),max_nfev=160);new=rectangle(sol.x,z);proj=project(new,pose);error=float(np.sqrt(np.mean(distances(sample(target,16),proj)**2)));agreement=iou(target,proj)
 original_edges=np.roll(q,-1,axis=0)-q;new_edges=np.roll(new,-1,axis=0)-new
 b['v1_roof_world']=b['roof_world'];b['roof_world']=new.tolist();b['rectangle']={'width':float(np.exp(sol.x[2])),'depth':float(np.exp(sol.x[3])),'angle_radians':float(sol.x[4]),'origin':new[0].tolist(),'source_roof_iou':agreement,'source_edge_rmse_px_at_1600':error};b['footprint_evidence']='Rectangular core fit to video-projected roof outline; perspective distortion is not retained as a skewed ground plan. Hidden depth is inferred.'
 # Preserve source masks and record the nearest facing side; new facade profiles are generated separately.
 for face in b.get('visible_facades',[]):
  j=face['edge']
  if j>=len(original_edges):continue
  old=original_edges[j,:2].copy();old/=np.linalg.norm(old);dirs=new_edges[:,:2]/np.linalg.norm(new_edges[:,:2],axis=1)[:,None];face['v2_edge']=int(np.argmax(dirs@old));face['v1_edge_length']=float(np.linalg.norm(original_edges[j,:2]))
 audit.append(dict(id=b['id'],corners_before=len(q),corners_after=4,perpendicular_error_degrees=0,source_roof_iou=round(agreement,4),source_edge_rmse_px_at_1600=round(error,3),width=round(b['rectangle']['width'],3),depth=round(b['rectangle']['depth'],3)))
(out/'inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));(out/'rectangle_fit_audit.json').write_text(json.dumps(audit,indent=2));print('RECTANGULAR_CORES',len(audit),'median IOU',np.median([x['source_roof_iou'] for x in audit]),'median edge RMS px',np.median([x['source_edge_rmse_px_at_1600'] for x in audit]));print('WORST',sorted(audit,key=lambda x:x['source_roof_iou'])[:8])
