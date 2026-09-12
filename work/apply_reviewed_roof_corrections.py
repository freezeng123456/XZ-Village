"""Corrections following 4K front/return comparisons and paired-ray checks."""
import json
from pathlib import Path
p=Path('work/buildings/roof_annotations.json');a=json.loads(p.read_text());d={b['id']:b for b in a['buildings']}
pairs=[('B025','R005',15.81,2.17),('B026','R006',16.92,3.22),('B027','R003',17.25,2.68)]
for bid,rid,h,gap in pairs:
 b=d[bid];r=d[rid];b.setdefault('secondary_observations',[]).append(dict(time=b['t'],roof=b['roof']));b.update(t=256,roof=r['roof'],height_override=h,height_locked=True,height_evidence=f'Manually identified front/return roof-centre pair triangulated through calibrated poses; closest-ray separation {gap} nominal m. Centre and scale remain approximate.');r['duplicate_of']=bid
d['R019']['duplicate_of']='B013';d['B013']['secondary_observations']=[dict(time=256,roof=d['R019']['roof'])]
d['B023']['secondary_observations']=[dict(time=44,roof=d['B023']['roof'],status='Rejected mixed trace spanning two neighbouring roofs')]
d['B023'].update(t=256,roof=[[1070,239],[1092,238],[1093,245],[1116,244],[1123,267],[1065,267]],height_override=12.21,height_locked=True,height_evidence='Paired front/return manual roof centres; 1.23 nominal m closest-ray gap; approximate')
if 'B035' not in d:a['buildings'].append(dict(id='B035',name='白色拱窗住宅后方独立白顶住宅',t=256,roof=[[996,225],[1020,225],[1022,233],[1047,234],[1058,270],[995,271]],type='flat',floors=3,height_override=12.7,height_locked=True,height_evidence='Separated from B023 after 4K review. Paired roof centres have 2.26 nominal m ray gap; approximate'))
d['O076']['roof']=[[118,467],[149,457],[143,483],[105,495]];d['O077']['roof']=[[148,458],[187,466],[182,485],[143,481]];d['O076']['floors']=2;d['O077']['floors']=2;d['O077']['parent']='O076';d['O076']['review_note']='Two separate connected tiled roof wings, corrected from 4K return crop; two storeys visible.'
d['B033']['parent']='B032'
for bid in ['B032','B033']:d[bid]['finish_style']='exposed_brick'
for bid in ['B004','R007','R008','R014','R015','R018','A042','A043','A047','A048','N010','N011']:d[bid]['finish_style']='weathered_concrete'
d['R024']['type']='solar';d['R030']['type']='metal'
p.write_text(json.dumps(a,ensure_ascii=False,indent=2));print('Corrected mixed roof trace, four cross-view duplicates, old connected roof wings and unfinished finishes.')
