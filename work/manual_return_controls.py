import json,numpy as np,pycolmap,cv2
from pathlib import Path
from scipy.spatial import cKDTree
from aerial_common import load_main
root=Path('work/aerial');a=json.loads((root/'alignment.json').read_text());R=np.array(a['rotation']);t=np.array(a['translation']);scale=a['scale']
rs=[load_main(root/'sfm'),pycolmap.Reconstruction(root/'sfm/sparse/2')]
coords=[[[705,259],[876,263],[919,476],[1021,517],[961,226]],[[331,200],[354,116],[793,84],[970,29],[264,70]]]
names=['bridge_village_corner','bridge_road_corner','pond_south_tip','road_south_outer','farmhouse_ground']
out=[]
for rec,ts,pts in zip(rs,[48,256],coords):
 im=next(i for i in rec.images.values() if i.name==f'f{ts:06.2f}.jpg');ps=[p for p in im.points2D if p.has_point3D()];uv=np.array([p.xy for p in ps]);xyz=np.array([rec.points3D[p.point3D_id].xyz for p in ps]);tree=cKDTree(uv)
 source=cv2.imread(str(root/f'sfm/images/{im.name}'));group=[]
 for k,p in enumerate(pts):
  ds,ix=tree.query(p,k=8); vals=xyz[ix]; world=vals@R.T*scale+t if ts==48 else vals
  group.append(dict(name=names[k],px=p,nearest_distances=ds.tolist(),nearest_px=uv[ix].tolist(),xyz=world.tolist(),raw=vals.tolist()))
  cv2.circle(source,tuple(p),6,(0,0,255),2);cv2.putText(source,str(k),(p[0]+7,p[1]),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,0,255),1)
  for v in uv[ix]:cv2.circle(source,tuple(v.astype(int)),2,(0,255,0),-1)
 cv2.imwrite(f'work/buildings/controls_{ts}.jpg',source);out.append(group)
Path('work/buildings/manual_control_candidates.json').write_text(json.dumps(out,indent=2));print(json.dumps([[dict(name=p['name'],distance=p['nearest_distances'][:3],xyz=p['xyz'][:3]) for p in g] for g in out],indent=2))
