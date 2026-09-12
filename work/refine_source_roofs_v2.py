"""Idempotent corrections recorded after direct source-camera visual review."""
from pathlib import Path
import json
base=Path('work/buildings/v2');path=base/'inventory.json';data=json.loads(path.read_text())
flat='O003 O008 O016 O020 O024 O041 O044 O045 O047 O054 O055 O056 O057 O058 O059 O064 O065 O090 O091 O094 O095'.split()
gable='O030 O060 O061 O063'.split();rejected=[]
for b in data['buildings']:
 if b['id'] in ['O069','R031']:
  rejected.append(dict(candidate=b,reason='Direct review of the amber source polygon shows vegetable garden and dirt path, not a building.'))
  continue
 if b['id'] in flat+gable:
  b.setdefault('roof_type_before_source_review',b['type']);b['type']='flat' if b['id'] in flat else 'gable';b['source_roof_review']='Corrected after direct source crop inspection'
 if b['id'].startswith('O') or b['id']=='D001':b['gable_ridge_axis']='x';b['ridge_evidence']='Row-house ridge continuity interpreted from source roof edges; approximate orientation'
for b in data['buildings']:
 if b['id'] in 'O031 O032 O033 O034 O035 O042 O060 O067 O068 O076 O077 O078 O083'.split():b['gable_ridge_axis']='y';b['ridge_evidence']='Direct source-camera review: visible ridge and tile channels cross the default row-house direction'
data['buildings']=[b for b in data['buildings'] if b['id'] not in ['O069','R031']]
path.write_text(json.dumps(data,ensure_ascii=False,indent=2))
if rejected:
 rp=base/'rejected_candidates.json';old=json.loads(rp.read_text()) if rp.exists() else [];merged={r['candidate']['id']:r for r in old+rejected};rp.write_text(json.dumps(list(merged.values()),ensure_ascii=False,indent=2))
print('SOURCE_ROOF_CORRECTIONS',len(flat)+len(gable),'RETAINED_UNITS',len(data['buildings']))
