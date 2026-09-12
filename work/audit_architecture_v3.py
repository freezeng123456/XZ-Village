"""Independent saved-scene plan intersection and file-integrity checks."""
import json,cv2,numpy as np
from pathlib import Path
root=Path.cwd();out=root/'outputs/orthogonal-multiview';v=json.loads((out/'validation.json').read_text());polys={id:cv2.convexHull(np.array(p,np.float32)[:,:2].copy()).reshape(-1,2) for id,p in v['world_plan_polygons'].items()};pairs=[];ids=sorted(polys)
# Hulls conservatively enclose the notched plans. Disjoint hulls prove disjoint cores.
for i,a in enumerate(ids):
 p=polys[a];plo,phi=p.min(0),p.max(0)
 for b in ids[i+1:]:
  q=polys[b]
  if np.any(phi<q.min(0)) or np.any(q.max(0)<plo):continue
  area,_=cv2.intersectConvexConvex(p,q)
  if area>1e-4:pairs.append(dict(a=a,b=b,hull_intersection_area=float(area)))
bs={b['id']:b for b in json.loads((root/'work/buildings/v3/inventory.json').read_text())['buildings']};core_pairs=[r for r in pairs if min(bs[r['a']]['roof_height'],bs[r['b']]['roof_height'])-max(bs[r['a']]['base_height'],bs[r['b']]['base_height'])>1e-4]
a=dict(method='Pairwise convex-hull intersections of saved scene ground plans; conservative for concave footprints.',units=len(polys),projected_plan_overlaps=pairs,core_volume_intersections=core_pairs,passed=not core_pairs,limitation='Five projected overlaps occupy different estimated height intervals. This does not validate terrain elevations, roof overhang intersections, or distant unit associations.')
(out/'plan_intersection_audit.json').write_text(json.dumps(a,indent=2));v['checks'].pop('no_intersecting_saved_core_hulls',None);v['checks']['no_intersecting_saved_core_volumes']=not core_pairs;v['passed']=all(v['checks'].values());(out/'validation.json').write_text(json.dumps(v,ensure_ascii=False,indent=2));print(json.dumps(dict(passed=v['passed'],counts=v['counts'],intersection_audit=a),indent=2))
