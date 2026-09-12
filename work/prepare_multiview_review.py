from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
r=Path('work/buildings/v3');r.mkdir(exist_ok=True);bs=json.loads(Path('work/buildings/v2/inventory.json').read_text())['buildings'];poses=json.loads(Path('work/buildings/visibility/poses.json').read_text());font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',25);ims={44:Image.open('work/buildings/source_44_4k.jpg'),256:Image.open(r/'source_256_4k.jpg')};cards=[];records=[]
def project(q,p):
 pc=q@np.array(p['rotation']).T+p['translation'];xy=pc[:,:2]/pc[:,2,None];return xy*(1+p['radial']*(xy*xy).sum(1))[:,None]*p['focal']+[800,450]
for b in bs:
 if not b['id'].startswith(('B','C','D','R')):continue
 card=Image.new('RGB',(1400,640),'#efeee8');d=ImageDraw.Draw(card);d.text((15,5),b['id']+' '+b['name'],font=font,fill='#182c35');points=np.array(b['roof_world']);base=points.copy();base[:,2]=b['base_height'];points=np.vstack([points,base]);rec={'id':b['id'],'views':{}}
 for j,t in enumerate([44,256]):
  p=poses[str(t)];px=project(points,p);roof=project(points[:4],p);lo=px.min(0)-[14,20];hi=px.max(0)+[14,20];scale=2.4;im=ims[t].crop(tuple(np.r_[lo,hi]*scale));dr=ImageDraw.Draw(im);q=(roof-lo)*scale;dr.line([tuple(x) for x in np.vstack([q,q[0]])],fill='#e7aa35',width=3);im=ImageOps.contain(im,(700,570));card.paste(im,(j*700+(700-im.width)//2,65+(570-im.height)//2));d.text((j*700+15,36),f'{t} 秒 · 当前屋顶投影黄线',font=font,fill='#34494f');rec['views'][t]={'crop_1600':np.r_[lo,hi].tolist(),'roof_px':roof.tolist()}
 card.save(r/(b['id']+'_both.jpg'),quality=94);cards.append(card);records.append(rec)
for i in range(0,len(cards),8):
 sheet=Image.new('RGB',(2100,1920),'#efeee8')
 for j,im in enumerate(cards[i:i+8]):sheet.paste(im.resize((1050,480)),((j%2)*1050,(j//2)*480))
 sheet.save(r/f'multiview_contact_{i//8:02}.jpg',quality=93)
(r/'multiview_review_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('TWO_VIEW_CARDS',len(cards))
