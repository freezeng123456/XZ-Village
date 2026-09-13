"""Source-specific facade opening proposals for visual review; no facade templates."""
import numpy as np,cv2,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path('work/rebuild4/architecture/facades');d=json.loads((P/'manifest.json').read_text());allrows=[];font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',12)
for e in d['entries']:
 bid=e['building_id'];face=e['face'];prefix=f'{bid}_f{face:02}';img=cv2.imread(str(P/(prefix+'.jpg')));visible=cv2.imread(str(P/(prefix+'_visible.png')),0)>0;rgb=img[...,::-1].astype(float);h,w=visible.shape;value=rgb.max(2);bright=np.percentile(value[visible],75) if visible.any() else 160;green=(rgb[...,1]>rgb[...,0]*1.05)&(rgb[...,1]>rgb[...,2]*.94)&(value<210)
 dark=value<bright*.76;mask=(dark|green)&visible;mask[:5]=False;mask[-5:]=False;mask[:,:4]=False;mask[:,-4:]=False;mask=ndmask=cv2.morphologyEx(mask.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((2,2),np.uint8));num,labels,stats,centroids=cv2.connectedComponentsWithStats(mask,8);boxes=[]
 for k,(x,y,ww,hh,area) in enumerate(stats[1:],1):
  if area<70 or ww<9 or hh<12 or ww>min(w*.82,180) or hh>min(h*.36,180):continue
  if ww/hh<.22 or ww/hh>4.5 or area/(ww*hh)<.30:continue
  vis=visible[y:y+hh,x:x+ww].mean()
  if vis<.72:continue
  # Window must have frame-sized clear margin, avoiding large occluding facade edges.
  pad=3;per=np.zeros((hh+pad*2,ww+pad*2),np.uint8);per[:pad]=1;per[-pad:]=1;per[:,:pad]=1;per[:,-pad:]=1;box=[int(x),int(y),int(x+ww),int(y+hh)];boxes.append(dict(box_px=box,visibility=float(vis),fill_ratio=float(area/(ww*hh)),status='unreviewed source component'))
 out=Image.fromarray(img[...,::-1]);dr=ImageDraw.Draw(out)
 for k,b in enumerate(boxes):
  dr.rectangle(tuple(b['box_px']),outline='#f93333',width=2);dr.text(tuple(b['box_px'][:2]),str(k),font=font,fill='yellow',stroke_width=1,stroke_fill='black')
 out.save(P/(prefix+'_openings.jpg'));allrows.append(dict(**e,opening_proposals=boxes))
(P/'opening_proposals.json').write_text(json.dumps(dict(entries=allrows,status='automatic proposals; not accepted architectural openings'),indent=2));print('PROPOSED',sum(len(r['opening_proposals']) for r in allrows),'faces',len(allrows))
