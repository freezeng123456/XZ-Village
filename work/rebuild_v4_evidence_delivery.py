import json,cv2,numpy as np,shutil
from pathlib import Path
from shapely.geometry import Polygon
from rebuild_v4_arch_geometry import project
P=Path('work/rebuild4/architecture');O=Path('/Users/zenghang/Documents/Codex/2026-09-12/jie/outputs/XZ-Village-Rebuilt-V4');d=json.loads((P/'village_mesh_input.json').read_text());bs=d['entries'];profiles=json.loads((P/'village_profiles.json').read_text());imgs=Path('work/rebuild4/sfm/images');audit={'units':len(bs),'profile_units':len(profiles['entries']),'unique_ids':len({b['id'] for b in bs}),'invalid_footprints':[],'nonpositive_wall_heights':[],'nonorthogonal_perimeters':[],'same_level_overlap_candidates':[],'scope':'geometry consistency checks; does not establish video coverage or architectural fidelity'}
polys=[]
for b in bs:
 q=np.array(b['footprint_world']);p=Polygon(q);polys.append(p)
 if not p.is_valid or p.area<.05:audit['invalid_footprints'].append(b['id'])
 if b['roof_edge_height']<=b['base_height']:audit['nonpositive_wall_heights'].append(b['id'])
 e=np.roll(q,-1,axis=0)-q;e/=np.linalg.norm(e,axis=1)[:,None];angle=np.degrees(np.arccos(np.clip((e*np.roll(e,-1,axis=0)).sum(1),-1,1)));err=np.min(np.abs(angle[:,None]-np.array([0,90,180])),axis=1)
 if err.max()>1:audit['nonorthogonal_perimeters'].append(dict(id=b['id'],max_deviation_degrees=float(err.max()),special=b.get('special_model')))
for i,a in enumerate(bs):
 for j,b in enumerate(bs[:i]):
  if abs(a['roof_edge_height']-b['roof_edge_height'])>.65 or abs(a['base_height']-b['base_height'])>1:continue
  over=polys[i].intersection(polys[j]).area/max(.01,min(polys[i].area,polys[j].area))
  if over>.18:audit['same_level_overlap_candidates'].append(dict(ids=[a['id'],b['id']],fraction=over,roof_types=[a['roof_type'],b['roof_type']]))
for sec in [0,44,64,80,90,120,256]:
 name=f'frame_{sec:03}.00.jpg';im=cv2.imread(str(imgs/name));N=0
 for b in bs:
  xy=np.array(b['footprint_world']);uv=project(np.c_[xy,np.full(len(xy),b['roof_edge_height'])],name)
  if not np.isfinite(uv).all() or uv[:,0].max()<0 or uv[:,0].min()>2400 or uv[:,1].max()<0 or uv[:,1].min()>1350:continue
  if (uv.max(0)-uv.min(0)).max()>2500:continue
  u=np.round(uv).astype(np.int32);c=(70,230,225) if b['roof_type'] not in ['solar','metal'] else (250,160,45);cv2.polylines(im,[u],True,c,2);center=np.round(uv.mean(0)).astype(int)
  if 0<center[0]<2380 and 0<center[1]<1340:
   cv2.putText(im,b['id'],tuple(center),cv2.FONT_HERSHEY_SIMPLEX,.43,(10,25,20),3,cv2.LINE_AA);cv2.putText(im,b['id'],tuple(center),cv2.FONT_HERSHEY_SIMPLEX,.43,(230,255,244),1,cv2.LINE_AA);N+=1
 cv2.imwrite(str(O/'evidence'/f'Roof_Identifiers_{sec:03}.jpg'),im,[cv2.IMWRITE_JPEG_QUALITY,94]);print('OVERLAY',sec,N)
for a,b in [(P/'village_mesh_input.json',O/'data/architecture_geometry.json'),(P/'village_profiles.json',O/'data/architecture_profiles.json'),(P/'final_duplicate_adjudication.json',O/'evidence/duplicate_adjudication.json'),(P/'facade_adjudication_audit.json',O/'evidence/facade_adjudication.json'),(P/'coordinates.json',O/'data/coordinate_system.json'),(Path('work/rebuild4/final_camera_audit/camera_audit.json'),O/'evidence/camera_audit.json'),(Path('work/rebuild4/final_camera_audit/frozen_inputs.json'),O/'evidence/frozen_camera_inputs.json'),(Path('work/rebuild4/holdout/audit.json'),O/'evidence/withheld_frame_audit.json')]:shutil.copy2(a,b)
(O/'evidence/input_geometry_audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
