"""Find compact elevated roof components in the frozen dense source surface.
These are source-supported fixture proposals, separate from manual pilot fixtures.
"""
import json,numpy as np,cv2
from scipy.spatial import cKDTree
from shapely.geometry import Polygon
from shapely import contains_xy
from rebuild_v4_arch_geometry import *
P=OUT;d=json.loads((P/'village_mesh_input.json').read_text());ss=np.load(P/'surface_points.npz');xyz=ss['xyz'];rgb=ss['rgb'];tree=cKDTree(xyz[:,:2]);results=[]
for b in d['entries']:
 if b['id'].startswith('P') or b['roof_type']!='flat' or b.get('source_role') in ['canopy','roof_room'] or b['roof_edge_height']-b['base_height']<5:continue
 xy=np.array(b['footprint_world']);center=xy.mean(0);rad=np.linalg.norm(xy-center,axis=1).max();ids=np.array(tree.query_ball_point(center,rad),int);roof=b['roof_edge_height'];sel=ids[(xyz[ids,2]>roof+.35)&(xyz[ids,2]<roof+4.0)];poly=Polygon(xy).buffer(-.25)
 if len(sel)<18 or poly.is_empty:continue
 sel=sel[contains_xy(poly,xyz[sel,0],xyz[sel,1])]
 if len(sel)<18:continue
 pts=xyz[sel];origin=pts[:,:2].min(0)-.6;ij=np.floor((pts[:,:2]-origin)/.30).astype(int);sz=ij.max(0)+3
 if np.prod(sz)>20000:continue
 grid=np.zeros(sz[::-1],np.uint8);grid[ij[:,1],ij[:,0]]=255;grid=cv2.dilate(grid,np.ones((3,3),np.uint8));n,ll,_,_=cv2.connectedComponentsWithStats(grid);groups=ll[ij[:,1],ij[:,0]]
 for k in range(1,n):
  chosen=sel[groups==k]
  if len(chosen)<18:continue
  q=xyz[chosen];siz=np.percentile(q[:,:2],95,axis=0)-np.percentile(q[:,:2],5,axis=0);top=float(np.percentile(q[:,2],95));height=top-roof;col=np.median(rgb[chosen],axis=0);rat=max(siz)/max(.01,min(siz))
  if not(.25<min(siz)<2.6 and max(siz)<3.0 and .65<height<3.7 and max(siz)*min(siz)<4.5):continue
  if col[1]>col[0]*1.2 or col[1]>col[2]*1.6:continue
  c=np.median(q[:,:2],axis=0);typ='tank' if rat<1.7 else 'heater';radius=float(np.clip(np.mean(siz)/2,.30,.94));stand=float(np.clip(height-1.2,.15,.85));record=dict(id=b['id'],type=typ,center_world=c.tolist(),radius=radius,height=float(np.clip(height-stand,.7,2.0)),stand=stand,source_points=len(q),rgb=col.astype(int).tolist(),z_top=top,status='compact elevated dense surface component; source roof appearance review pending');results.append(record)
(P/'source_roof_fixtures.json').write_text(json.dumps(results,indent=2));print('FIXTURES',len(results),flush=True)
for sec in [0,44,64,90,120,256]:
 name=f'frame_{sec:06.2f}.jpg';im=cv2.imread(str(ROOT/'sfm/images'/name))
 for e in results:
  q=np.r_[e['center_world'],e['z_top']];pp=project([q],name)[0]
  if not np.isfinite(pp).all() or not(0<pp[0]<2400 and 0<pp[1]<1350):continue
  x,y=np.round(pp).astype(int);cv2.circle(im,(x,y),8,(30,245,250),2);cv2.putText(im,e['id'],(x+6,y-6),cv2.FONT_HERSHEY_SIMPLEX,.37,(0,0,0),3);cv2.putText(im,e['id'],(x+6,y-6),cv2.FONT_HERSHEY_SIMPLEX,.37,(30,245,250),1)
 cv2.imwrite(str(P/f'roof_fixture_review_{sec:03}.jpg'),im)
