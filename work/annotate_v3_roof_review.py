from pathlib import Path
import numpy as np,json
from PIL import Image,ImageDraw,ImageFont
r=Path('work/buildings/v3');p=json.loads(Path('work/buildings/visibility/poses.json').read_text())['256'];bs=json.loads(Path('work/buildings/v2/inventory.json').read_text())['buildings'];f=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',21);im=Image.open(r/'source_256_4k.jpg').resize((1600,900))
def project(q):
 pc=q@np.array(p['rotation']).T+p['translation'];xy=pc[:,:2]/pc[:,2,None];return xy*(1+p['radial']*(xy*xy).sum(1))[:,None]*p['focal']+[800,450]
for ids,name in [(['B002','B003','B004','B005','B006','B007','B008','B009','B010','B011','B012','B013','B014','B015'],'modern_east'),(['B016','B017','B018','B019','B020','B021','B022','B023','B024'],'pond_east'),(['B025','B026','B027','R001','R002','R003','R004','R005','R006','R007','R008'],'pond_west')]:
 coords=[project(np.array(b['roof_world'])) for b in bs if b['id'] in ids];xy=np.vstack(coords);lo=np.maximum([0,0],np.floor(xy.min(0)-45)).astype(int);hi=np.minimum([1600,900],np.ceil(xy.max(0)+60)).astype(int);scale=3;crop=im.crop(tuple(np.r_[lo,hi])).resize(tuple((hi-lo)*scale));d=ImageDraw.Draw(crop)
 for x in range((lo[0]//20+1)*20,hi[0],20):d.line(((x-lo[0])*scale,0,(x-lo[0])*scale,crop.height),fill=(150,150,150),width=1);d.text(((x-lo[0])*scale+2,3),str(x),font=f,fill='red')
 for y in range((lo[1]//20+1)*20,hi[1],20):d.line((0,(y-lo[1])*scale,crop.width,(y-lo[1])*scale),fill=(150,150,150),width=1);d.text((3,(y-lo[1])*scale+2),str(y),font=f,fill='red')
 for b in bs:
  if b['id'] not in ids:continue
  q=(project(np.array(b['roof_world']))-lo)*scale
  for k,x in enumerate(q):d.text(tuple(x),str(k),font=f,fill='yellow')
  d.text(tuple(q.mean(0)),b['id'],font=f,fill='#00eeff')
 crop.save(r/(name+'_coords.jpg'),quality=96);print(name,lo,hi)
