from pathlib import Path
import json,numpy as np,cv2
root=Path.cwd();folder=root/'work/buildings/v2';path=folder/'inventory.json';data=json.loads(path.read_text());bs=data['buildings'];poses=json.loads((root/'work/buildings/visibility/poses.json').read_text())
code=(root/'work/fit_rectangular_architecture.py').read_text();exec('def project'+code.split('def project',1)[1].split('for b in data',1)[0],globals())
rows=[];overlaps=[]
for b in bs:
 q=np.array(b['roof_world']);proj=project(q,poses[str(b['t'])]);target=np.array(b['roof']);error=float(np.sqrt(np.mean(distances(sample(target,16),proj)**2)));agreement=iou(target,proj);b['rectangle']['source_roof_iou_after_placement']=agreement;b['rectangle']['source_edge_rmse_px_after_placement']=error;rows.append(dict(id=b['id'],iou=agreement,edge_rmse_px_at_1600=error,source_time=b['t'],shift_m=float(np.linalg.norm(b['rectangle'].get('nonintersection_shift_m',[0,0])))))
for i,a in enumerate(bs):
 q=np.array(a['roof_world'],np.float32)
 for b in bs[i+1:]:
  if min(a['roof_height'],b['roof_height'])<=max(a['base_height'],b['base_height'])+.08:continue
  r=np.array(b['roof_world'],np.float32)
  if np.any(q[:,:2].max(0)<r[:,:2].min(0)) or np.any(r[:,:2].max(0)<q[:,:2].min(0)):continue
  area,_=cv2.intersectConvexConvex(np.ascontiguousarray(q[:,:2]),np.ascontiguousarray(r[:,:2]))
  if area>.01:overlaps.append(dict(a=a['id'],b=b['id'],area_m2=area))
result=dict(units=len(bs),median_roof_iou=float(np.median([r['iou'] for r in rows])),median_edge_rmse_px=float(np.median([r['edge_rmse_px_at_1600'] for r in rows])),p90_edge_rmse_px=float(np.percentile([r['edge_rmse_px_at_1600'] for r in rows],90)),minimum_iou=min(r['iou'] for r in rows),adjusted_units=sum(r['shift_m']>.001 for r in rows),maximum_translation_m=max(r['shift_m'] for r in rows),core_intersections=overlaps,per_building=rows,metric_boundary='Projected rectangular main-roof outline compared with original video annotation at 1600x900, after collision correction. Excludes hip/gable overhang, facade likeness and survey accuracy; narrow distant annotations can have low IoU.')
path.write_text(json.dumps(data,ensure_ascii=False,indent=2));(folder/'final_alignment_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='per_building'},indent=2))
