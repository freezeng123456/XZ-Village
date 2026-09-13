"""Create source-evidence orthographic rasters in frozen final architectural axes.
Raster images are review evidence only and are never model textures.
"""
import json,time,sys
from pathlib import Path
import numpy as np,cv2,open3d as o3d
from scipy import ndimage as nd
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rebuild_v4_arch_geometry import ROOT,OUT,A,O,S,local
src=ROOT/'village_surface/scene_dense.ply';assert (src.parent/'done.json').exists()
p=o3d.io.read_point_cloud(str(src));xyz=local(np.asarray(p.points)).astype(np.float32);rgb=(np.asarray(p.colors)*255).round().astype(np.uint8);normal=(np.asarray(p.normals)@A.T).astype(np.float32);print('POINTS',len(xyz),flush=True)
np.savez_compressed(OUT/'surface_points.npz',xyz=xyz,rgb=rgb,normal=normal)
# Bounded support: remove extreme outliers using full-image registered SfM cloud extents.
lo=np.percentile(xyz[:,:2],.1,axis=0)-2;hi=np.percentile(xyz[:,:2],99.9,axis=0)+2;res=.2;shape=np.ceil((hi-lo)/res).astype(int);W,H=shape;print('BOUNDS',lo,hi,W,H,flush=True)
ix=np.floor((xyz[:,:2]-lo)/res).astype(int);ok=(ix[:,0]>=0)&(ix[:,0]<W)&(ix[:,1]>=0)&(ix[:,1]<H)&(np.abs(normal[:,2])>.5);ix=ix[ok];z=xyz[ok,2];col=rgb[ok];nor=normal[ok];ids=ix[:,1]*W+ix[:,0]
# Median within the topmost 35 cm suppresses single extreme depth points.
order=np.lexsort((z,ids));ids=ids[order];z=z[order];col=col[order];nor=nor[order];starts=np.r_[0,np.flatnonzero(np.diff(ids))+1];ends=np.r_[starts[1:],len(ids)];counts=ends-starts;choose=starts+np.floor((counts-1)*.70).astype(int);unique=ids[starts]
def grid(data,fill):
 dims=(H,W)+data.shape[1:];a=np.full(dims,fill,dtype=data.dtype);a.reshape((H*W,)+data.shape[1:])[unique]=data[choose];return a
height=grid(z,np.nan);color=grid(col,0);norm=grid(nor,0);coverage=np.zeros((H,W),np.uint16);coverage.ravel()[unique]=counts
valid=np.isfinite(height);dist,indices=nd.distance_transform_edt(~valid,return_indices=True);filled=height[tuple(indices)];filled=nd.median_filter(filled,size=3);near=dist<4
# Ground only supports measuring building height; candidate ground is reviewed later.
coarse=cv2.resize(filled,None,fx=.2,fy=.2,interpolation=cv2.INTER_AREA);k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(31,31));dtm=cv2.morphologyEx(coarse,cv2.MORPH_OPEN,k);dtm=nd.gaussian_filter(dtm,2);dtm=cv2.resize(dtm,(W,H),interpolation=cv2.INTER_LINEAR)
np.savez_compressed(OUT/'surface_raster.npz',height=height,filled=filled,dtm=dtm,color=color,normal=norm,coverage=coverage,near=near,lo=lo,res=res)
cc=color[tuple(indices)];cc[~near]=[25,28,33];Image.fromarray(cc[::-1]).save(OUT/'evidence_orthographic_color.png')
gray=np.clip((filled-dtm)/22,0,1);heat=cv2.applyColorMap((gray*255).astype(np.uint8),cv2.COLORMAP_TURBO)[...,::-1];heat[~near]=[25,28,33];Image.fromarray(heat[::-1]).save(OUT/'evidence_height_above_ground.png')
(OUT/'surface_raster_metadata.json').write_text(json.dumps(dict(point_count=len(xyz),bounds=[lo.tolist(),hi.tolist()],resolution=res,width=int(W),height=int(H),notes=['colour raster is source evidence only, excluded from final Blender materials','DTM is a morphological initial estimate, building ground contacts need visual review']),indent=2));print('RASTER_READY',flush=True)
