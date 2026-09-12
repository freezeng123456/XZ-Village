"""Separate inferred rectangular cores while keeping source-supported large houses stable."""
from pathlib import Path
import json,numpy as np,cv2
root=Path.cwd();path=root/'work/buildings/v2/inventory.json';data=json.loads(path.read_text());bs=data['buildings'];original={b['id']:np.array(b['roof_world']) for b in bs};p=[np.array(b['roof_world']) for b in bs];locked={'B005','B006','B008','B010','B012','B014','O001'};history=[]
def separation(a,b):
 axes=[]
 for q in [a,b]:
  for j in [0,1]:e=q[j+1,:2]-q[j,:2];axes.append(e/np.linalg.norm(e))
 overlaps=[]
 for axis in axes:
  aa=a[:,:2]@axis;bb=b[:,:2]@axis;ov=min(aa.max(),bb.max())-max(aa.min(),bb.min())
  if ov<=.005:return None
  # A contained interval needs translation to the nearest outer separating edge.
  plus=aa.max()-bb.min();minus=bb.max()-aa.min();direction=axis if plus<minus else -axis;overlaps.append((min(plus,minus),direction))
 return min(overlaps,key=lambda x:x[0])
for it in range(80):
 changed=0
 for i,a in enumerate(bs):
  for j in range(i+1,len(bs)):
   if np.any(p[i][:,:2].max(0)<p[j][:,:2].min(0)) or np.any(p[j][:,:2].max(0)<p[i][:,:2].min(0)):continue
   if a['roof_height']<bs[j]['base_height']+.08 or bs[j]['roof_height']<a['base_height']+.08:continue
   sep=separation(p[i],p[j])
   if sep is None:continue
   penetration,direction=sep;delta=direction*(penetration+.035);areaA=a['rectangle']['width']*a['rectangle']['depth'];areaB=bs[j]['rectangle']['width']*bs[j]['rectangle']['depth'];wa=0 if a['id'] in locked else 1/max(areaA,6);wb=0 if bs[j]['id'] in locked else 1/max(areaB,6)
   if wa+wb==0:raise RuntimeError('Overlapping source pilots need visual resolution')
   p[i][:,:2]-=delta*wa/(wa+wb);p[j][:,:2]+=delta*wb/(wa+wb);history.append(dict(a=a['id'],b=bs[j]['id'],penetration=float(penetration)));changed+=1
 if not changed:break
else:raise RuntimeError('Unresolved rectangle packing')
# The untouched original landmark is an immutable obstacle.
landmark=np.array([[0,0,10.65],[7.5,0,10.65],[7.5,8.5,10.65],[0,8.5,10.65]])
for i,b in enumerate(bs):
 if separation(landmark,p[i]) is not None:raise RuntimeError('New unit overlaps original landmark: '+b['id'])
changes=[]
for b,q in zip(bs,p):
 shift=q.mean(0)-original[b['id']].mean(0);b['roof_world']=q.tolist();b['rectangle']['origin']=q[0].tolist();b['rectangle']['nonintersection_shift_m']=shift[:2].tolist()
 if np.linalg.norm(shift)>.001:changes.append(dict(id=b['id'],shift_m=shift[:2].tolist(),distance_m=float(np.linalg.norm(shift))))
path.write_text(json.dumps(data,ensure_ascii=False,indent=2));(root/'work/buildings/v2/placement_corrections.json').write_text(json.dumps(dict(iterations=it+1,adjusted=changes,resolved_pairs=history,remaining_core_intersections=0),indent=2));print('CORE_OVERLAPS_RESOLVED',len(changes),'units',it+1,'iterations','max shift',max([c['distance_m'] for c in changes] or [0]));print(sorted(changes,key=lambda c:c['distance_m'],reverse=True)[:8])
