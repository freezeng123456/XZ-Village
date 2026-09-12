"""Inferred completion for small or partially visible buildings, user-authorized.

Roof placement follows the supplied imagery; small facade details may be
completed plausibly rather than exactly, per the user's clarification.
"""
import json
from pathlib import Path
p=Path('work/buildings/roof_annotations.json');a=json.loads(p.read_text());a['buildings']=[b for b in a['buildings'] if not b['id'].startswith(('F','G','C'))]
far88=[
 [[201,154],[235,159],[243,169],[194,166]],[[112,162],[160,159],[184,169],[129,176]],
 [[144,201],[197,194],[209,212],[160,218]],[[76,220],[121,212],[135,229],[78,236]],
 [[48,176],[93,174],[114,183],[57,191]],[[0,182],[38,181],[65,190],[26,200],[0,197]],
 [[154,223],[194,216],[207,230],[165,237]],[[86,246],[114,244],[127,256],[83,266]],
 [[27,250],[69,241],[89,252],[45,267]],[[0,280],[30,274],[49,287],[15,297],[0,294]],
 [[0,143],[31,142],[36,160],[1,166]],[[108,153],[136,151],[153,161],[111,166]],
 [[78,302],[105,297],[119,304],[89,313]],[[38,293],[73,285],[89,294],[54,306]]
]
for i,poly in enumerate(far88,1):a['buildings'].append(dict(id=f'F{i:03d}',name=f'北侧村群住宅 {i:03d}',t=88,roof=poly,type='flat',floors=1 if i>12 else (4 if i in [1,11] else 3),inferred_detail_authorized=True,evidence='Roof outline from video; obscured details plausibly completed as authorized by user.'))
# Small roof quads are inferred from visible roof-centre/width/depth cues.
far44=[(20,36,27,7),(50,31,25,7),(12,58,23,7),(37,63,25,7),(70,58,27,8),(99,41,27,7),(125,33,25,7),(152,35,26,7),(127,54,28,8),(164,63,29,8),(185,51,24,7),(207,49,24,7),(224,39,22,7),(179,84,31,9),(146,100,31,9),(105,85,30,9),(75,102,31,9),(34,96,28,9),(10,92,21,8),(79,130,36,9),(163,135,36,10),(208,116,32,9),(239,130,34,10),(274,108,34,10),(294,89,34,9),(340,111,35,10),(371,101,36,10),(406,102,37,10),(443,111,33,9),(483,116,33,9),(523,120,33,9),(528,92,28,8),(555,96,28,8),(478,87,29,8),(434,84,30,8),(388,88,29,8)]
for j,(x,y,w,d) in enumerate(far44,15):
 poly=[[x-w*.42,y-d*.5],[x+w*.46,y-d*.38],[x+w*.5,y+d*.45],[x-w*.5,y+d*.5]];a['buildings'].append(dict(id=f'F{j:03d}',name=f'北侧远景住宅 {j:03d}',t=44,roof=poly,type='flat',floors=3,inferred_detail_authorized=True,evidence='Small visible roof unit; inferred perimeter and facade detail, not precise reconstruction.'))
old=[(8,133,25,11),(36,139,28,12),(62,147,31,12),(93,155,28,12),(119,143,29,12),(143,159,30,12),(174,151,31,12),(200,144,29,12),(224,158,30,12),(254,145,28,12),(26,167,32,14),(61,183,33,14),(92,192,32,14),(126,181,30,13),(151,192,31,13),(183,186,31,13),(212,195,30,13),(17,198,31,15),(54,215,31,14),(80,226,29,14)]
for j,(x,y,w,d) in enumerate(old,1):a['buildings'].append(dict(id=f'G{j:03d}',name=f'西北侧瓦房单元 {j:03d}',t=44,roof=[[x-w*.4,y-d*.5],[x+w*.5,y-d*.15],[x+w*.4,y+d*.5],[x-w*.5,y+d*.1]],type='gable',floors=1,inferred_detail_authorized=True,evidence='Distant tile-roof unit; estimated eave/ridge, unseen walls and openings.'))
front=[('南端路边旧灰楼',[[584,520],[765,533],[775,581],[548,580]],2,'flat'),('南端在建砖房',[[171,752],[413,787],[451,899],[62,899]],1,'construction'),('南端旧白色折角住宅',[[278,604],[425,614],[456,641],[417,713],[183,711],[186,658]],2,'flat'),('南端左侧白色住宅',[[0,509],[91,492],[137,522],[108,577],[0,582]],3,'flat'),('南端小型附属房',[[374,544],[416,545],[435,579],[357,581]],1,'flat')]
for j,(name,poly,floors,kind) in enumerate(front,1):a['buildings'].append(dict(id=f'C{j:03d}',name=name,t=20,roof=poly,type=kind,floors=floors,finish_style='exposed_brick' if kind=='construction' else 'weathered_concrete',inferred_detail_authorized=True,partial=j in [2,4],evidence='Additional southern building visible during the approach; occluded extent estimated.'))
p.write_text(json.dumps(a,ensure_ascii=False,indent=2));print('Added',len(far88)+len(far44)+len(old)+len(front),'remaining candidate units; annotation entries',len(a['buildings']))
