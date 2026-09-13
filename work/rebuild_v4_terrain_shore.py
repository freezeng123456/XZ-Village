"""Exact pond cuts remove coarse-grid sawtooth banks."""
from shapely import intersects as shape_intersects, polygons as shape_polygons
pond_union=unary_union([poly for poly,_,_ in water]);fa=np.array(faces);quads=terrain[fa,:2];hit=shape_intersects(shape_polygons(quads),pond_union);kept=fa[~hit].tolist();extra_v=[]
for face in fa[hit]:
 vv=terrain[face];mn=vv[:,:2].min(0);mx=vv[:,:2].max(0);part=Polygon(vv[:,:2]).difference(pond_union)
 if part.is_empty:continue
 for piece in ([part] if part.geom_type=='Polygon' else list(part.geoms)):
  if piece.geom_type!='Polygon':continue
  for tri in geometry_triangulate(piece):
   if not piece.covers(tri):continue
   xy=np.array(tri.exterior.coords)[:3];z=zground(xy);off=len(terrain)+len(extra_v);extra_v.extend(np.c_[xy,z].tolist());kept.append([off,off+1,off+2])
if extra_v:terrain=np.vstack([terrain,extra_v])
faces=kept
# Low retaining banks hide the vertical cut beneath the water line.
for poly,z,label in water:
 for piece in ([poly] if poly.geom_type=='Polygon' else list(poly.geoms)):
  if piece.geom_type!='Polygon':continue
  pts=np.array(piece.exterior.coords);vs=[];fs=[]
  for a,b in zip(pts,pts[1:]):
   ts=np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/1.5)+1));q=a+(b-a)*ts[:,None];top=zground(q);top=np.maximum(z+.08,top)
   for i in range(len(q)-1):
    off=len(vs);vs.extend([[*q[i],top[i]],[*q[i+1],top[i+1]],[*q[i+1],z-.25],[*q[i],z-.25]]);fs.append([off,off+1,off+2,off+3])
  mesh.append(dict(name=label+' retaining earth',kind='bank',vertices=vs,faces=fs))
print('EXACT SHORE',int(hit.sum()),'intersected terrain cells',flush=True)
