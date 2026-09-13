"""Bounded village DSM and multi-scale ground candidates from the full surface."""
import numpy as np,cv2,json
from scipy import ndimage as nd
from PIL import Image
from pathlib import Path
P=Path('work/rebuild4/architecture');s=np.load(P/'surface_points.npz');xyz=s['xyz'];rgb=s['rgb'];normal=s['normal'];lo=np.array([-680.,-310.]);hi=np.array([200.,610.]);res=.2;W,H=np.ceil((hi-lo)/res).astype(int);ij=np.floor((xyz[:,:2]-lo)/res).astype(int);keep=(ij[:,0]>=0)&(ij[:,0]<W)&(ij[:,1]>=0)&(ij[:,1]<H)&(xyz[:,2]>-10)&(xyz[:,2]<150);xyz=xyz[keep];rgb=rgb[keep];normal=normal[keep];ij=ij[keep];ids=ij[:,1]*W+ij[:,0];order=np.lexsort((xyz[:,2],ids));ids=ids[order];xyz=xyz[order];rgb=rgb[order];normal=normal[order];starts=np.r_[0,np.flatnonzero(np.diff(ids))+1];ends=np.r_[starts[1:],len(ids)];counts=ends-starts;unique=ids[starts];print('POINTS',len(xyz),'RASTER',W,H,flush=True)
def array(data,quantile=.7,fill=0):
 idx=starts+np.floor((counts-1)*quantile).astype(int);a=np.full((H*W,)+data.shape[1:],fill,data.dtype);a[unique]=data[idx];return a.reshape((H,W)+data.shape[1:])
height=array(xyz[:,2],.8,np.nan);low=array(xyz[:,2],.05,np.nan);color=array(rgb);norm=array(normal);coverage=np.zeros((H,W),np.uint16);coverage.ravel()[unique]=counts;valid=np.isfinite(height);dist,ind=nd.distance_transform_edt(~valid,return_indices=True);filled=nd.median_filter(height[tuple(ind)],size=3);low=nd.median_filter(low[tuple(ind)],size=3);near=dist<5;cc=color[tuple(ind)];cc[~near]=[25,28,33]
coarse=cv2.resize(low,None,fx=.2,fy=.2,interpolation=cv2.INTER_AREA);base={}
for win in [31,61,101]:
 k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(win,win));dt=cv2.morphologyEx(coarse,cv2.MORPH_OPEN,k);dt=nd.gaussian_filter(dt,1.5);base['ground'+str(win)]=cv2.resize(dt,(W,H),interpolation=cv2.INTER_LINEAR)
np.savez_compressed(P/'village_raster.npz',height=height,filled=filled,low=low,dtm=base['ground61'],color=cc,normal=norm,coverage=coverage,near=near,lo=lo,res=res,**base)
Image.fromarray(cc[::-1]).save(P/'village_ortho.png');heat=cv2.applyColorMap((np.clip((filled-base['ground61'])/22,0,1)*255).astype(np.uint8),cv2.COLORMAP_TURBO)[...,::-1];heat[~near]=[25,28,33];Image.fromarray(heat[::-1]).save(P/'village_height.png');print('DONE',flush=True)
