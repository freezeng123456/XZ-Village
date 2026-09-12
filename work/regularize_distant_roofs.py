"""Plausible depth completion where tiny near-horizon traces are ill-conditioned.

Keep the annotated projected roof centre and approximate frontage direction.
Do not convert a handful of blurred vertical pixels into 60 m deep houses.
"""
import json,numpy as np
from pathlib import Path
p=Path('work/buildings/architecture_candidates.json');a=json.loads(p.read_text());changed=[]
for b in a['buildings']:
 if not (b['id'].startswith('F') and b['t']==44 or b['id'].startswith('G')):continue
 q=np.array(b['roof_world']);u=q[1]-q[0];u[2]=0;width=np.linalg.norm(u);u/=width;v=np.array([-u[1],u[0],0]);center=q.mean(0);width=float(np.clip(width,5,15));depth=8.5 if b['type']=='flat' else 7.;q=np.array([center-u*width/2-v*depth/2,center+u*width/2-v*depth/2,center+u*width/2+v*depth/2,center-u*width/2+v*depth/2]);b['roof_world']=q.tolist();b['footprint_evidence']='Projected roof centre and approximate frontage from video; hidden roof depth and rectangular outline inferred (8.5 m modern / 7 m tile unit). Tiny horizon traces do not support measured depth.';b['inferred_detail_authorized']=True;changed.append(b['id'])
p.write_text(json.dumps(a,ensure_ascii=False,indent=2));Path('work/buildings/regularized_ids.json').write_text(json.dumps(changed));print('Regularized',len(changed),'distant footprints')
