"""Source-located roads, water outlines, agricultural plots and measured canopy cover.
All surfaces are editable geometry with semantic procedural materials, never photos.
"""
import json,cv2,numpy as np
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,triangulate as geometry_triangulate
from shapely import contains_xy
from rebuild_v4_arch_geometry import *
P=OUT;d=json.loads((P/'village_mesh_input.json').read_text());r=np.load(P/'village_raster.npz');lo=r['lo'];res=float(r['res']);ground=nd.gaussian_filter(r['ground101'],2.0);ss=np.load(P/'surface_points.npz');xyz=ss['xyz'][::2];rgb=ss['rgb'][::2];normal=ss['normal'][::2];sources=[];ground_controls=[];control_tree=None;control_xyz=None;flat_cache={}
def zground(xy):
 xy=np.asarray(xy);p=(xy-lo)/res;shape=p.shape[:-1];p=p.reshape(-1,2);zz=nd.map_coordinates(ground,[p[:,1],p[:,0]],order=1,mode='nearest')
 if control_tree is not None:
  dist,ii=control_tree.query(xy.reshape(-1,2),k=min(8,len(control_xyz)));weights=1/np.maximum(.35,dist)**2;control_z=np.sum(control_xyz[ii,2]*weights,axis=1)/weights.sum(1);weight=np.clip((12-dist[:,0])/7,0,1);zz=zz*(1-weight)+control_z*weight
 return zz.reshape(shape)
def observed_ground_z(pp,name):
 if name not in flat_cache:
  im,cam=camera(name);ww=world(xyz);cp=ww@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation;uv=cam.img_from_cam(cp);ok=np.isfinite(uv).all(1)&(cp[:,2]>0)&(uv[:,0]>=0)&(uv[:,0]<2400)&(uv[:,1]>=0)&(uv[:,1]<1350);ij=np.floor(np.nan_to_num(uv,nan=-1e5)*.5).astype(int);buf=np.full((675,1200),np.inf,np.float32);np.minimum.at(buf,(ij[ok,1],ij[ok,0]),cp[ok,2]*S);vis=ok.copy();vis[ok]=cp[ok,2]*S<buf[ij[ok,1],ij[ok,0]]+.40;col=rgb.astype(float);flat=vis&(np.abs(normal[:,2])>.87)&(col[:,1]<col[:,0]*1.17)&(col[:,1]<col[:,2]*1.45);gp=(xyz[:,:2]-lo)/res;prior=nd.map_coordinates(ground,[gp[:,1],gp[:,0]],order=1,mode='nearest');flat&=(xyz[:,2]<prior+1.7)&(xyz[:,2]>prior-2.5);ii=np.flatnonzero(flat);flat_cache[name]=(cKDTree(uv[ii]),xyz[ii])
 tree,q=flat_cache[name];dist,ind=tree.query(pp,k=48);zs=[]
 for dd,ii in zip(dist,ind):
  use=dd<min(22,max(7,dd[0]+4));zs.append(float(np.median(q[ii[use],2])) if use.sum()>3 else np.nan)
 return np.array(zs)
def intersect_ground(points,sec):
 name=f'frame_{sec:06.2f}.jpg';pp=np.array(points,float)*2400/2048;C,ray=rays(pp,name);t=(3-C[2])/ray[:,2]
 for _ in range(30):
  q=C+ray*t[:,None];tnew=(zground(q[:,:2])-C[2])/ray[:,2];t=.55*t+.45*tnew
 zz=observed_ground_z(pp,name);ok=np.isfinite(zz)
 if ok.any():
  zz[~ok]=np.interp(np.flatnonzero(~ok),np.flatnonzero(ok),zz[ok]);t=(zz-C[2])/ray[:,2]
 return C+ray*t[:,None]
roads=[]
def road(sec,pts,width,label):
 global control_tree,control_xyz
 qq=intersect_ground(pts,sec);zz=nd.median_filter(qq[:,2],size=3,mode='nearest');qq[:,2]=zz;pp=np.array(pts,float)*2400/2048;C,ray=rays(pp,f'frame_{sec:06.2f}.jpg');qq=C+ray*((zz-C[2])/ray[:,2])[:,None];q=qq[:,:2];poly=LineString(q).buffer(width/2,cap_style='round',join_style='round');roads.append(poly)
 for a,b in zip(qq,qq[1:]):
  for t in np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/2))):ground_controls.append((a+(b-a)*t).tolist())
 control_xyz=np.array(ground_controls);control_tree=cKDTree(control_xyz[:,:2]);sources.append(dict(kind='road',label=label,source_image=f'frame_{sec:06.2f}.jpg',source_pixels=(np.array(pts)*2400/2048).tolist(),width_in_provisional_units=width,ground_control_points=qq.tolist()));return q
road(0,[(1101,1150),(1113,958),(1129,842),(1161,745),(1204,659),(1188,523),(1167,420),(1133,303),(1097,194),(1065,142),(1030,76),(995,0)],5.6,'southern main lane')
road(64,[(1140,1150),(1149,925),(1145,807),(1140,744),(1128,661),(1117,593),(1070,479),(1085,371),(1104,290),(1075,268),(997,254),(960,243)],5.8,'pond-side main road and north bend')
road(90,[(1165,1150),(991,965),(848,800),(737,663),(639,530),(556,435),(508,352),(478,306),(460,288)],6.0,'northern residential road')
road(120,[(544,1150),(587,961),(601,872),(634,745),(691,632),(766,571),(831,545),(935,517)],7.6,'hillside avenue')
road(90,[(523,313),(656,333),(895,368),(1111,411),(1335,460),(1556,510),(1788,582),(2017,635)],5.7,'cross-village northern road')
road(0,[(159,1149),(295,974),(320,890),(343,826),(391,747),(445,677),(478,583),(511,503),(570,420),(626,344),(681,272)],3.2,'southern inner lane')
road(256,[(408,1150),(435,1063),(469,943),(501,827),(548,690),(596,561),(650,454),(670,406)],2.7,'central old-house lane')
road(256,[(740,1099),(756,936),(775,815),(802,717),(861,649),(922,575),(972,492),(1009,433)],2.7,'east old-house lane')
road(64,[(129,1149),(248,1034),(387,944),(520,861),(639,773),(732,704),(845,659)],4.5,'main pond west promenade')
road(256,[(39,202),(300,168),(456,146),(649,118),(845,92),(1046,66)],4.5,'pond bridge road')
road(0,[(1189,508),(1427,500),(1678,490),(1900,484),(2045,482)],1.4,'southern farm access')
road(0,[(1148,216),(1366,192),(1528,134),(1692,133),(1851,151),(2013,183)],1.3,'upper farm access')
road(120,[(2014,517),(1770,458),(1618,429),(1567,368),(1540,318),(1516,263),(1486,208),(1472,162)],2.0,'hillside farm access')
exec((Path('work')/'rebuild_v4_ground_conform.py').read_text())
water=[]
def pond(sec,pts,label):
 z={'main village pond':-1.85,'northern roadside pond':-1.75,'pond behind isolated building':-1.0}[label];q=intersect_z(np.array(pts,float)*2400/2048,f'frame_{sec:06.2f}.jpg',z)[:,:2];poly=Polygon(q).buffer(0);water.append((poly,z,label));sources.append(dict(kind='water',label=label,source_image=f'frame_{sec:06.2f}.jpg',source_pixels=(np.array(pts)*2400/2048).tolist(),level=z))
pond(256,[(464,169),(1022,109),(1008,141),(1048,167),(1028,224),(991,252),(947,270),(818,286),(704,287),(659,279),(624,298),(578,293),(577,280),(507,296),(486,288),(490,257),(443,259)],'main village pond')
pond(256,[(0,190),(70,175),(239,144),(214,103),(87,100),(29,114),(11,143)],'northern roadside pond')
pond(64,[(1113,501),(1270,512),(1292,648),(1183,644),(1148,655),(1137,601)],'pond behind isolated building')
fields=[]
def field(sec,pts,style,label):
 q=intersect_ground(pts,sec)[:,:2];poly=Polygon(q).buffer(0)
 if poly.area<5:return
 fields.append((poly,style,label));sources.append(dict(kind='agricultural_plot',label=label,style=style,source_image=f'frame_{sec:06.2f}.jpg',source_pixels=(np.array(pts)*2400/2048).tolist()))
field(0,[(1215,263),(1393,237),(1482,328),(1380,373),(1195,365)],'plowed','south upper plot')
field(0,[(1460,179),(1670,175),(1905,253),(1608,281)],'mulch','plastic-mulched rows')
field(0,[(1569,295),(1874,268),(1950,310),(1641,343)],'crops','dark green row crop')
field(0,[(1208,412),(1400,412),(1471,472),(1371,491),(1221,485)],'crops','small southern vegetable garden')
field(0,[(1254,554),(1563,527),(1694,649),(1535,711),(1290,727)],'plowed','southern large open plot')
field(0,[(1298,746),(1469,751),(1564,792),(1549,875),(1380,912),(1265,827)],'crops','southern green plot')
field(0,[(1301,961),(1571,884),(1726,977),(1530,1117),(1208,1127)],'plowed','southern foreground plot')
field(0,[(1729,546),(1908,519),(2043,542),(2043,791),(1925,714)],'plowed','southeast plot')
field(64,[(1261,825),(1491,790),(1736,858),(1541,922),(1264,988)],'plowed','field opposite main pond')
field(64,[(1245,1015),(1547,946),(1866,1035),(1793,1147),(1240,1147)],'plowed','pond foreground field')
field(64,[(1346,686),(1482,662),(1598,697),(1456,757),(1298,771)],'crops','field beside isolated house')
field(64,[(1294,356),(1449,355),(1495,439),(1300,447)],'crops','public garden vegetables')
field(64,[(1621,461),(1882,397),(2000,491),(1861,545),(1665,536)],'plowed','northeast open plot')
field(90,[(937,547),(1150,517),(1267,557),(1099,628)],'plowed','plot behind northern row')
field(90,[(1196,619),(1508,544),(1646,575),(1312,704)],'plowed','northern diagonal field')
field(90,[(1448,729),(1849,607),(1996,657),(1612,816)],'plowed','east diagonal field')
field(90,[(77,625),(378,553),(493,622),(207,736)],'crops','northwest vegetable plots')
field(90,[(37,826),(241,751),(363,813),(184,916)],'plowed','northwest bare plot')
field(120,[(1710,526),(1950,577),(2039,608),(2039,710),(1678,630)],'plowed','hill road right fields')
field(120,[(1530,304),(1717,309),(1859,344),(1744,385),(1573,366)],'plowed','hill upper field')
field(120,[(1607,396),(1809,410),(1960,448),(1795,463),(1650,445)],'crops','hill middle green rows')
# Native frame44 supplies the missing continuous farmland mosaic east of the main road.
field(44,[(1312,1150),(2047,1150),(2047,991),(1318,978)],'mulch','frame44 foreground parallel beds')
field(44,[(1314,969),(1998,970),(1978,915),(1320,913)],'crops','frame44 foreground green strip')
field(44,[(1320,900),(1956,901),(1836,806),(1318,802)],'plowed','frame44 foreground tilled plot')
field(44,[(1412,791),(1827,792),(1790,722),(1402,720)],'mulch','frame44 garden behind small shed')
field(44,[(1440,679),(1637,680),(1456,541),(1356,547),(1350,622)],'plowed','frame44 bend wedge field')
field(44,[(1671,670),(1888,646),(1572,529),(1483,540)],'plowed','frame44 diagonal middle plot')
field(44,[(1911,640),(2047,615),(2047,504),(1812,509),(1698,524)],'crops','frame44 east green middle rows')
field(44,[(1390,523),(1555,509),(1417,431),(1344,441)],'mulch','frame44 northern road corner beds')
field(44,[(1573,506),(1783,488),(1626,419),(1451,434)],'crops','frame44 northern green beds')
field(44,[(1806,485),(2017,468),(1816,385),(1646,415)],'crops','frame44 northern upper green plot')
field(44,[(1303,417),(1548,393),(1493,359),(1268,382)],'plowed','frame44 northern upper brown strip')
field(44,[(1261,373),(1582,339),(1538,319),(1244,350)],'mulch','frame44 northern upper mulch strip')
field(44,[(1241,344),(1525,314),(1484,292),(1222,321)],'crops','frame44 north field green strip')
field(44,[(1216,312),(1480,285),(1429,266),(1210,288)],'plowed','frame44 north field back strip')

# Serialize triangulated semantic ground surfaces with smooth terrain elevation.
mesh=[]
def surface(poly,kind,z=None,name=None):
 if poly.is_empty:return
 if poly.geom_type!='Polygon':
  for g in poly.geoms:surface(g,kind,z,name)
  return
 # Bound triangulation by the actual outline, including union-created holes.
 vs=[];fs=[]
 for tri in geometry_triangulate(poly):
  if not poly.covers(tri):continue
  q=np.array(tri.exterior.coords)[:3];todo=[q]
  while todo:
   q=todo.pop();edges=np.roll(q,-1,axis=0)-q;length=np.linalg.norm(edges,axis=1);k=int(length.argmax())
   if z is None and length[k]>1.25:
    j=(k+1)%3;other=(k+2)%3;mid=(q[k]+q[j])/2;todo.extend([np.array([q[k],mid,q[other]]),np.array([mid,q[j],q[other]])]);continue
   zz=zground(q)+.20 if z is None else np.full(3,z);start=len(vs);vs.extend(np.column_stack([q,zz]).tolist());fs.append([start,start+1,start+2])
 mesh.append(dict(name=name or kind,kind=kind,vertices=vs,faces=fs))
# Resolve overlapping observations of the same agricultural plot, latest native outline wins.
claimed=Polygon();unique_fields=[]
for poly,style,label in reversed(fields):
 clean=poly.difference(claimed);claimed=unary_union([claimed,poly])
 if not clean.is_empty:unique_fields.append((clean,style,label))
fields=list(reversed(unique_fields))
roofpoly=unary_union([Polygon(b['footprint_world']).buffer(.15) for b in d['entries']]);roadpoly=unary_union(roads).difference(roofpoly);surface(roadpoly,'road',name='Source road network');fieldcuts=unary_union([roadpoly,roofpoly]);fieldrows=[]
for i,(poly,style,label) in enumerate(fields):
 poly=poly.difference(fieldcuts)
 if poly.is_empty:continue
 surface(poly,style,name=label)
 if poly.geom_type!='Polygon':continue
 pts=np.array(poly.exterior.coords);edges=np.diff(pts,axis=0);axis=edges[np.linalg.norm(edges,axis=1).argmax()];axis/=np.linalg.norm(axis);side=np.array([-axis[1],axis[0]]);pp=pts@np.stack([axis,side],axis=1);mn=pp.min(0);mx=pp.max(0);spacing=1.3 if style in ['crops','mulch'] else .95
 for y in np.arange(mn[1],mx[1],spacing):
  ends=np.array([[mn[0]-1,y],[mx[0]+1,y]])@np.stack([axis,side]);cut=LineString(ends).intersection(poly)
  lines=[cut] if cut.geom_type=='LineString' else list(getattr(cut,'geoms',[]))
  for line in lines:
   if line.geom_type!='LineString' or line.length<.5:continue
   points=[line.interpolate(t).coords[0] for t in np.linspace(0,line.length,max(2,int(line.length)+1))];q=np.array(points);fieldrows.append(dict(points=np.column_stack([q,zground(q)+.13]).tolist(),kind=style,width=.24 if style=='crops' else (.20 if style=='mulch' else .08)))
water=[(poly.difference(roadpoly.buffer(.45)).difference(roofpoly),z,label) for poly,z,label in water]
for poly,z,label in water:surface(poly,'water',z,label)
# Canopy locations come from observed green, elevated dense surfaces.
h=xyz[:,2]-zground(xyz[:,:2]);c=rgb.astype(float)/255;green=(c[:,1]>c[:,0]*1.055)&(c[:,1]>c[:,2]*1.20)&(c[:,1]>.13);ok=green&(h>2.4)&(h<23)&(xyz[:,0]>-680)&(xyz[:,0]<170)&(xyz[:,1]>-310)&(xyz[:,1]<600);q=xyz[ok];col=c[ok];grid=np.floor(q[:,:2]/4.5).astype(int);keys=grid[:,0].astype(np.int64)*10000+grid[:,1];order=np.argsort(keys);keys=keys[order];q=q[order];col=col[order];starts=np.r_[0,np.flatnonzero(np.diff(keys))+1,len(keys)];trees=[];tree_exclusion=unary_union([roofpoly.buffer(.55)]+[poly.buffer(1.6) for poly,_,_ in water])
for i,j in zip(starts,starts[1:]):
 if j-i<24:continue
 points=q[i:j];center=np.median(points[:,:2],axis=0);spread=np.percentile(points[:,:2],90,axis=0)-np.percentile(points[:,:2],10,axis=0)
 if min(spread)<1.3 or tree_exclusion.contains(Point(center)):continue
 base=float(zground(center));top=float(np.percentile(points[:,2],88));height=top-base
 if height<3:continue
 trees.append(dict(xy=center.tolist(),base=base,height=height,radius=float(np.clip(np.mean(spread)*.82,1.55,3.7)),color=np.median(col[i:j],axis=0).tolist(),source_points=int(j-i)))
xy=txy.copy();terrain=np.column_stack([xy,zground(xy)]);ii=np.arange(len(xy)).reshape(len(terrain_ys),len(terrain_xs));faces=np.stack([ii[:-1,:-1].ravel(),ii[:-1,1:].ravel(),ii[1:,1:].ravel(),ii[1:,:-1].ravel()],axis=1).tolist();
exec((Path('work')/'rebuild_v4_terrain_shore.py').read_text())
env=dict(surfaces=mesh,field_rows=fieldrows,trees=trees,terrain_vertices=terrain.tolist(),terrain_faces=faces,terrain_grid_resolution=terrain_res,ground_control_points=ground_controls,water_outlines=[dict(xy=np.array(part.exterior.coords).tolist(),z=z) for poly,z,_ in water for part in ([poly] if poly.geom_type=='Polygon' else list(poly.geoms)) if part.geom_type=='Polygon'],source_annotations=sources,status='source-located semantic environment with inferred foliage geometry and crop-row detail')
(P/'village_environment.json').write_text(json.dumps(env));print('ENVIRONMENT',len(mesh),'surfaces',len(fieldrows),'rows',len(trees),'observed canopy cells',flush=True)
# The same source overlays expose alignment independently of final materials.
for sec in [0,64,90,120,256]:
 name=f'frame_{sec:06.2f}.jpg';im=cv2.imread(str(ROOT/'sfm/images'/name))
 for item in mesh:
  if not item['vertices']:continue
  v=np.array(item['vertices']);uv=project(v,name);cc=(40,220,250) if item['kind']=='road' else ((255,210,30) if item['kind']=='water' else (30,220,70))
  for face in item['faces']:
   pp=uv[face]
   if np.isfinite(pp).all() and (pp[:,0].max()>0) and (pp[:,0].min()<2400) and (pp[:,1].max()>0) and (pp[:,1].min()<1350):cv2.polylines(im,[np.round(pp).astype(int)],True,cc,1)
 for t in trees[::4]:
  pp=project([[*t['xy'],t['base']+t['height']]],name)[0]
  if np.isfinite(pp).all() and 0<pp[0]<2400 and 0<pp[1]<1350:cv2.circle(im,tuple(np.round(pp).astype(int)),3,(180,255,20),-1)
 cv2.imwrite(str(P/f'environment_source_review_{sec:03}.jpg'),im,[cv2.IMWRITE_JPEG_QUALITY,93])
