"""Fit an orthogonal perimeter while retaining source concavities and roof height."""
import numpy as np
from scipy.optimize import least_squares
from rebuild_v4_arch_geometry import project,intersect_z

def orthogonal_outline(pixels,image,z,other_observations=None):
 pixels=np.asarray(pixels,float);q=intersect_z(pixels,image,z)[:,:2];edges=np.roll(q,-1,axis=0)-q;ang=np.arctan2(edges[:,1],edges[:,0]);weight=np.linalg.norm(edges,axis=1)
 # Four-fold orientation mean, insensitive to which side of a building is observed.
 yaw=np.angle(np.sum(weight*np.exp(4j*ang)))/4
 def rot(a):return np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
 pq=q@rot(yaw);e=np.roll(pq,-1,axis=0)-pq;horizontal=np.abs(e[:,0])>np.abs(e[:,1]);N=len(q)
 def groups(axis):
  parent=list(range(N))
  def root(i):
   while parent[i]!=i:i=parent[i]
   return i
  for i,h in enumerate(horizontal):
   if (h and axis==1) or (not h and axis==0):parent[root((i+1)%N)]=root(i)
  labels=[root(i) for i in range(N)];unique=list(dict.fromkeys(labels));return np.array([unique.index(i) for i in labels]),len(unique)
 gx,nx=groups(0);gy,ny=groups(1);xx=np.array([np.mean(pq[gx==k,0]) for k in range(nx)]);yy=np.array([np.mean(pq[gy==k,1]) for k in range(ny)]);start=np.r_[yaw,xx,yy]
 def vertices(p):return np.column_stack([np.column_stack([p[1:1+nx][gx],p[1+nx:][gy]])@rot(p[0]).T,np.full(N,z)])
 def resid(p):
  res=(project(vertices(p),image)-pixels).ravel().tolist()
  if other_observations:
   for name,indices,pix in other_observations:res.extend((project(vertices(p)[indices],name)-pix).ravel())
  return res
 sol=least_squares(resid,start,loss='soft_l1',f_scale=2,max_nfev=600)
 verts=vertices(sol.x);err=np.array(resid(sol.x)).reshape(-1,2)
 return verts,dict(yaw=float(sol.x[0]),source_vertex_errors_px=np.linalg.norm(err,axis=1).tolist(),rms_px=float(np.sqrt(np.mean(err**2))),max_vertex_error_px=float(np.max(np.linalg.norm(err,axis=1))),unique_x=nx,unique_y=ny,edges=len(q))
