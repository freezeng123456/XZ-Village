"""Prepare the editable pilot geometry and fixed source cameras for neutral review."""
import json,numpy as np,pycolmap as pc
from pathlib import Path
from scipy.spatial import Delaunay
from shapely.geometry import Polygon,Point,box
from shapely import contains_xy
from rebuild_v4_arch_geometry import *
p=OUT;data=json.loads((p/'pilot_fitted.json').read_text());r=np.load(p/'village_raster.npz');lo=r['lo'];res=float(r['res']);ground=r['ground101'];H,W=ground.shape
for b in data['entries']:
 xy=np.array(b['footprint_world']);cent=xy.mean(0);i,j=np.floor((cent-lo)/res).astype(int);b['base_height']=float(ground[np.clip(j,0,H-1),np.clip(i,0,W-1)])+.12;b['ground_status']='provisional broad-scale terrain surface, visible contact verification pending'
 if b['roof_type']=='hip':
  yaw=b['fit']['yaw'];R=np.array([[np.cos(yaw),-np.sin(yaw)],[np.sin(yaw),np.cos(yaw)]]);localxy=xy@R;poly=Polygon(localxy);xs=np.unique(np.round(localxy[:,0],4));ys=np.unique(np.round(localxy[:,1],4));rects=[]
  for ia,x0 in enumerate(xs):
   for x1 in xs[ia+1:]:
    for ja,y0 in enumerate(ys):
     for y1 in ys[ja+1:]:
      rec=box(x0,y0,x1,y1)
      if rec.area<2 or not poly.buffer(.005).covers(rec):continue
      rects.append(rec)
  rects=[rr for rr in rects if not any(ss.area>rr.area+.01 and ss.buffer(.005).covers(rr) for ss in rects)];xmin,ymin,xmax,ymax=poly.bounds;xx=np.arange(xmin,xmax,.28);yy=np.arange(ymin,ymax,.28);gx,gy=np.meshgrid(xx,yy);pts=np.column_stack([gx.ravel(),gy.ravel()]);pts=pts[contains_xy(poly,pts[:,0],pts[:,1])];boundary=[]
  for a,z in zip(localxy,np.roll(localxy,-1,axis=0)):
   N=max(2,int(np.ceil(np.linalg.norm(z-a)/.22)));boundary.extend(a+(z-a)*t for t in np.linspace(0,1,N,endpoint=False))
  pts=np.r_[pts,np.array(boundary)];tri=Delaunay(pts).simplices;centers=pts[tri].mean(1);tri=tri[contains_xy(poly.buffer(.003),centers[:,0],centers[:,1])];hei=np.zeros(len(pts));pitch=.52
  for rect in rects:
   a,bb,c,d=rect.bounds;v=np.min(np.column_stack([pts[:,0]-a,c-pts[:,0],pts[:,1]-bb,d-pts[:,1]]),axis=1);hei=np.maximum(hei,v*pitch)
  ridge_max=max(.5,b.get('ridge_height',b['roof_edge_height']+2)-b['roof_edge_height']);hei=np.minimum(hei,ridge_max);ww=pts@R.T;v=np.column_stack([ww,hei+b['roof_edge_height']]);b['roof_mesh']=dict(vertices=v.tolist(),faces=tri.tolist(),method='intersecting hip roof planes over maximal orthogonal roof rectangles',pitch=pitch,max_rise=float(max(hei)),maximal_rectangles=[list(rr.bounds) for rr in rects])
# Ground patch is a real mesh, with no photographic color.
xs=np.arange(-105,5,2);ys=np.arange(-65,80,2);gx,gy=np.meshgrid(xs,ys);ii=np.floor((gx-lo[0])/res).astype(int);jj=np.floor((gy-lo[1])/res).astype(int);gz=ground[np.clip(jj,0,H-1),np.clip(ii,0,W-1)];verts=np.column_stack([gx.ravel(),gy.ravel(),gz.ravel()]);faces=[]
for j in range(len(ys)-1):
 for i in range(len(xs)-1):
  a=j*len(xs)+i;faces.append([a,a+1,a+len(xs)+1,a+len(xs)])
data['ground_mesh']=dict(vertices=verts.tolist(),faces=faces)
rec=pc.Reconstruction(ROOT/'village_surface/sparse');cameras=[]
for sec in [44,256,48,248]:
 name=f'frame_{sec:06.2f}.jpg';im=next(im for im in rec.images.values() if im.name==name);cam=rec.cameras[im.camera_id];R=im.cam_from_world().rotation.matrix()@A.T;cameras.append(dict(name=f'source_{sec:03}',image=name,R=R.tolist(),center=local(im.projection_center()).tolist(),width=cam.width,height=cam.height,params=cam.params.tolist(),source_image=str((ROOT/'village_surface/images'/name).resolve())))
data['cameras']=cameras;(p/'pilot_mesh_input.json').write_text(json.dumps(data,ensure_ascii=False));print([(b['id'],round(b['base_height'],2),round(b['roof_edge_height'],2),b.get('roof_mesh',{}).get('max_rise')) for b in data['entries']])
