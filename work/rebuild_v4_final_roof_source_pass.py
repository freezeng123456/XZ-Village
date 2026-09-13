import json,numpy as np
from pathlib import Path
P=Path('work/rebuild4/architecture');d=json.loads((P/'village_mesh_input.json').read_text());ps=json.loads((P/'village_profiles.json').read_text());g={b['id']:b for b in d['entries']};p={b['id']:b for b in ps['entries']};changes=[]
for k in ['V0031','V0032','V0059','V0151','V0157','V0474']:
 b=g[k];old=b.get('observed_surface_plane');coef=np.array(old or [0,0,b['roof_edge_height']],float);slope=np.linalg.norm(coef[:2]);coef[:2]*=.065/max(slope,.001);coef[2]=b['roof_edge_height']-np.dot(np.mean(b['footprint_world'],axis=0),coef[:2]);b['observed_surface_plane']=coef.tolist();b['roof_plane_review']='native source shows shallow white sheet roof; mixed-surface dense plane rejected; shallow pitch is simplified';changes.append(dict(id=k,old_plane=old,new_plane=coef.tolist(),status=b['roof_plane_review']))
for k,rise in [('V0052',.70),('V0146',.65),('V0198',.55)]:
 b=g[k];b['roof_type']='hip_metal';b['ridge_height']=b['roof_edge_height']+rise;b['roof_plane_review']='source two-pitch corrugated roof replaces erroneous single sloping sheet';changes.append(dict(id=k,new_type='pitched corrugated metal',rise=rise,status=b['roof_plane_review']))
k='V0143';g[k]['observed_surface_plane']=[0,0,g[k]['roof_edge_height']];g[k]['ridge_height']=g[k]['roof_edge_height']+.75;changes.append(dict(id=k,status='source tiled courtyard canopy rebuilt with two pitches and eave-height supports'))
(P/'village_mesh_input.json').write_text(json.dumps(d,ensure_ascii=False));(P/'final_roof_source_adjudication.json').write_text(json.dumps(dict(entries=changes),indent=2,ensure_ascii=False));print('CHANGED',[x['id'] for x in changes])
src=Path('work/rebuild_v4_build_architecture.py');s=src.read_text().replace('  sheet_roof(B,b,p,H,rm);return B.done()',"  if typ in ['gable','hip_metal']:pitched_roof(B,b,p,H,rm)\n  else:sheet_roof(B,b,p,H,rm)\n  return B.done()");src.write_text(s)
