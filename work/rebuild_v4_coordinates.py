"""Establish a shared architectural coordinate system from source geometry."""
import json
from pathlib import Path
import cv2,numpy as np,pycolmap as pc
from scipy.optimize import least_squares
root=Path('work/rebuild4');out=root/'architecture';out.mkdir(exist_ok=True)
r=pc.Reconstruction(root/'sfm/sparse_final/0');ims={im.name:im for im in r.images.values() if im.has_pose};rng=np.random.default_rng(5201)
im=ims['frame_044.00.jpg'];cam=r.cameras[im.camera_id];R=im.cam_from_world().rotation.matrix();C=im.projection_center()
xy=[];pts=[]
for p in im.points2D:
 if p.has_point3D() and 1630<p.xy[0]<2350 and 830<p.xy[1]<1330:xy.append(p.xy);pts.append(r.points3D[p.point3D_id].xyz)
pts=np.array(pts);best=[]
for i in range(1500):
 a,b,c=pts[rng.choice(len(pts),3,False)];n=np.cross(b-a,c-a);n/=np.linalg.norm(n);inside=np.flatnonzero(np.abs((pts-a)@n)<.004)
 if len(inside)>len(best):best=inside
center=pts[best].mean(0);_,_,V=np.linalg.svd(pts[best]-center);up=V[-1]
if up@(C-center)<0:up=-up
initial=up.copy();normals=[];weights=[];sources=[]
for sec in [0,28,44,64,96,244,256,262]:
 name=f'frame_{sec:06.2f}.jpg';im=ims[name];cam=r.cameras[im.camera_id];R=im.cam_from_world().rotation.matrix();gray=cv2.imread(str(root/'sfm/images'/name),0)
 lines=cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(gray)[0]
 for line in lines.reshape(-1,4):
  a,b=line[:2],line[2:];ln=np.linalg.norm(b-a)
  if ln<35:continue
  uv=cam.cam_from_img(np.array([a,b]));ray=np.column_stack([uv,np.ones(2)]);n=R.T@np.cross(ray[0],ray[1]);n/=np.linalg.norm(n)
  if abs(n@initial)<.18:normals.append(n);weights.append(min(ln,180));sources.append([name,line.tolist()])
N=np.array(normals);W=np.array(weights);bestscore=-1
for i in range(7000):
 v=np.cross(*N[rng.choice(len(N),2,False)]);v/=np.linalg.norm(v)
 if abs(v@initial)<np.cos(np.deg2rad(12)):continue
 use=np.abs(N@v)<.0035;score=W[use].sum()
 if score>bestscore:bestscore=score;bestv=v;bestuse=use
for i in range(4):
 _,_,V=np.linalg.svd(N[bestuse]*np.sqrt(W[bestuse,None]));up=V[-1];bestuse=np.abs(N@up)<.0035
if up@initial<0:up=-up
im=ims['frame_044.00.jpg'];cam=r.cameras[im.camera_id];R=im.cam_from_world().rotation.matrix();C=im.projection_center()
def ground(pixel):
 ray=R.T@np.r_[cam.cam_from_img(np.array(pixel,float)),1.];return C+ray*((center-C)@initial/(ray@initial))
origin=ground([1440,825]);direction=ground([1440,710])-ground([1455,1190]);y=direction-up*(direction@up);y/=np.linalg.norm(y);x=np.cross(y,up);A=np.stack([x,y,up]);scale=100.0
result=dict(origin=origin.tolist(),world_to_local_rotation=A.tolist(),scale=scale,scale_status='provisional metres per SfM unit; no surveyed physical dimension',ground_plane_point=center.tolist(),ground_plane_normal=initial.tolist(),vertical=up.tolist(),field_points=len(pts),field_plane_inliers=len(best),vertical_candidate_lines=len(N),vertical_retained_lines=int(bestuse.sum()),vertical_ground_angle_degrees=float(np.rad2deg(np.arccos(up@initial))),source='final joint SfM; field plane and robust multi-camera architectural vertical lines',axes='x cross road, y road towards distant end in frame 44, z source architectural vertical')
(out/'coordinates.json').write_text(json.dumps(result,indent=2));(out/'vertical_line_evidence.json').write_text(json.dumps([s for s,k in zip(sources,bestuse) if k],indent=2));print(result)
