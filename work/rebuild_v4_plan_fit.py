"""Rectilinear roof-plan fitting shared by point and image-plane evidence."""
import numpy as np,cv2
from scipy.optimize import minimize_scalar
from scipy.ndimage import binary_fill_holes
from shapely.geometry import Polygon,box
def footprint(pts):
 xy=pts[:,:2];ctr=np.median(xy,axis=0);dd=xy-ctr;rect=cv2.minAreaRect(dd.astype(np.float32));ang=np.deg2rad(rect[2])
 def rotation(a):return np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
 def area(a):
  q=dd@rotation(a);mn,mx=np.percentile(q,[.8,99.2],axis=0);return np.prod(mx-mn)
 opt=minimize_scalar(area,bounds=(ang-.12,ang+.12),method='bounded');ang=float(opt.x);R=rotation(ang);q=dd@R;mn,mx=np.percentile(q,[.6,99.4],axis=0);mn-=.16;mx+=.16;poly=box(*mn,*mx)
 # Detect large missing corners in the roof plan. Small support gaps remain geometry uncertainty.
 pitch=.35;ss=np.ceil((mx-mn)/pitch).astype(int)+1;grid=np.zeros((ss[1],ss[0]),np.uint8);ij=np.floor((q-mn)/pitch).astype(int);ok=(ij>=0).all(1)&(ij<ss).all(1);grid[ij[ok,1],ij[ok,0]]=1;grid=cv2.morphologyEx(grid,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));grid=binary_fill_holes(grid).astype(np.uint8)
 rawpoly=poly;cuts=[]
 for flipx,flipy in [(0,0),(1,0),(0,1),(1,1)]:
  g=grid[::-1] if flipy else grid;g=g[:,::-1] if flipx else g;best=None
  for ny in range(5,max(6,int(g.shape[0]*.68))):
   for nx in range(5,max(6,int(g.shape[1]*.68))):
    if g[:ny,:nx].mean()>.06:continue
    ar=nx*ny*pitch**2
    if ar<rawpoly.area*.07:continue
    if best is None or ar>best[0]:best=(ar,nx,ny)
  if best:
   _,nx,ny=best;xa,xb=(mx[0]-nx*pitch,mx[0]+.01) if flipx else (mn[0]-.01,mn[0]+nx*pitch);ya,yb=(mx[1]-ny*pitch,mx[1]+.01) if flipy else (mn[1]-.01,mn[1]+ny*pitch);cut=box(xa,ya,xb,yb);trial=poly.difference(cut)
   if trial.geom_type=='Polygon' and trial.area>rawpoly.area*.56:poly=trial;cuts.append([xa,ya,xb,yb])
 coords=np.array(poly.exterior.coords[:-1])@R.T+ctr
 if not Polygon(coords).exterior.is_ccw:coords=coords[::-1]
 return coords,dict(yaw=ang,bounds_local=[mn.tolist(),mx.tolist()],origin=ctr.tolist(),missing_corner_cuts=cuts,point_plan_area=float(Polygon(coords).area))
