"""Camera and geometric primitives for evidence-based editable architecture."""
from pathlib import Path
import json,numpy as np,pycolmap as pc,cv2
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parent/'rebuild4';OUT=ROOT/'architecture';D=json.loads((OUT/'coordinates.json').read_text());A=np.array(D['world_to_local_rotation']);O=np.array(D['origin']);S=D['scale'];REC=pc.Reconstruction(ROOT/'sfm/sparse_final/0');IMS={im.name:im for im in REC.images.values() if im.has_pose}
def local(p):return (np.asarray(p)-O)@A.T*S
def world(p):return np.asarray(p)@A/S+O
def camera(name):
 im=IMS[name];return im,REC.cameras[im.camera_id]
def project(p,name):
 im,cam=camera(name);w=world(p);q=w@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation;return cam.img_from_cam(q)
def rays(pixels,name):
 im,cam=camera(name);q=cam.cam_from_img(np.asarray(pixels,float));direc=np.column_stack([q,np.ones(len(q))])@im.cam_from_world().rotation.matrix()@A.T;return local(im.projection_center()),direc

def intersect_z(pixels,name,z):
 C,d=rays(pixels,name);return C+d*((z-C[2])/d[:,2])[:,None]
def triangulate(obs):
 n=[];v=[]
 for name,pix in obs:
  C,dr=rays([pix],name);dr=dr[0]/np.linalg.norm(dr[0]);M=np.eye(3)-np.outer(dr,dr);n.append(M);v.append(M@C)
 return np.linalg.lstsq(np.concatenate(n),np.concatenate(v),rcond=None)[0]
def sparse_inside(name,poly):
 im,_=camera(name);poly=np.asarray(poly,np.float32);pts=[]
 for p in im.points2D:
  if p.has_point3D() and cv2.pointPolygonTest(poly,tuple(p.xy),False)>0:pts.append(local(REC.points3D[p.point3D_id].xyz))
 return np.array(pts)
def fit_rect(obs,initial=None):
 # corners are A,B,C,D with edges AB depth, BC width.
 if initial is None:
  corners=[]
  for lab in ['A','B','C','D']:
   ob=[(x['image'],x['corners'][lab]) for x in obs if lab in x['corners']]
   if len(ob)>1:corners.append((lab,triangulate(ob)))
  d=dict(corners);depth=np.linalg.norm(d['B'][:2]-d['A'][:2]);width=np.linalg.norm(d['D'][:2]-d['A'][:2]);yaw=np.arctan2(*(d['B'][:2]-d['A'][:2])[::-1]);initial=np.r_[d['A'][:2],np.mean([x[1][2] for x in corners]),yaw,depth,width]
 def xyz(p):
  x,y,z,a,d,w=p;u=np.array([np.cos(a),np.sin(a)]);v=np.array([-np.sin(a),np.cos(a)]);q=np.array([[x,y],[x,y]+u*d,[x,y]+u*d+v*w,[x,y]+v*w]);return np.column_stack([q,np.full(4,z)])
 # perpendicular can have either sign
 if initial is not None:
  p1=initial.copy();p2=initial.copy();p2[-1]*=-1
 def residual(p):
  q=xyz(p);res=[]
  for ob in obs:
   ij=['ABCD'.index(k) for k in ob['corners']];res.extend((project(q[ij],ob['image'])-np.array(list(ob['corners'].values()))).ravel())
  return np.array(res)
 opts=[least_squares(residual,p,loss='soft_l1',f_scale=2,max_nfev=600) for p in [p1,p2]];sol=min(opts,key=lambda x:np.sum(residual(x.x)**2));return xyz(sol.x),dict(params=sol.x.tolist(),pixel_residuals=residual(sol.x).reshape(-1,2).tolist(),rms_px=float(np.sqrt(np.mean(residual(sol.x)**2))))
if __name__=='__main__':
 data=json.loads((OUT/'pilot_observations.json').read_text());results={}
 for entry in data['entries']:
  if not entry['roof_observations']:continue
  obs=[]
  for ob in entry['roof_observations']:
   obs.append(dict(image=ob['image'],corners=ob.get('corners',dict(zip(ob.get('corner_names',[]),ob.get('ordered_corners',[]))))))
  q,fit=fit_rect(obs);results[entry['id']]=dict(corners=q.tolist(),fit=fit);print(entry['id'],q,fit,flush=True)
 (OUT/'initial_roof_fits.json').write_text(json.dumps(results,indent=2))
