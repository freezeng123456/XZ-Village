"""Multi-threshold rectified-wall opening proposals, respecting source visibility."""
import cv2,numpy as np,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path('work/rebuild4/architecture/facades');entries=json.loads((P/'manifest.json').read_text())['entries'];result=[];font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',12)
for e in entries:
 prefix=f'{e["building_id"]}_f{e["face"]:02}';im=cv2.imread(str(P/(prefix+'.jpg')));vis=cv2.imread(str(P/(prefix+'_visible.png')),0)>0;h,w=vis.shape;pp=e['pixels_per_unit'];gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);channels=[gray,im[...,2]];proposals=[]
 for ch in channels:
  ms=cv2.MSER_create(5,int(.15*pp*pp),int(12*pp*pp),.3,.2,200,1.01,.003,3);regions,boxes=ms.detectRegions(ch)
  for region,(x,y,ww,hh) in zip(regions,boxes):
   if hh<.83*pp or hh>3.1*pp or ww<.43*pp or ww>4.5*pp or ww/hh<.17 or ww/hh>3.5:continue
   if x<4 or x+ww>w-4 or y<4 or y+hh>h-4:continue
   if vis[y:y+hh,x:x+ww].mean()<.68:continue
   rect=np.zeros(ch.shape,np.uint8);cv2.rectangle(rect,(x,y),(x+ww-1,y+hh-1),1,-1);margin=cv2.dilate(rect,np.ones((9,9),np.uint8)).astype(bool)&(~rect.astype(bool))&vis
   if margin.sum()<25:continue
   local=ch[y:y+hh,x:x+ww];contrast=np.median(ch[margin])-np.median(local)
   if contrast<12:continue
   extent=len(region)/(ww*hh)
   if extent<.38:continue
   # Outer frame rectangles are preferred to individual panes without becoming whole-wall shadows.
   proposals.append(dict(box_px=[int(x),int(y),int(x+ww),int(y+hh)],contrast=float(contrast),extent=float(extent),score=float(contrast*np.sqrt(ww*hh)*(extent**.3))))
 proposals.sort(key=lambda a:-a['score']);keep=[]
 for p in proposals:
  a=np.array(p['box_px']);area=(a[2]-a[0])*(a[3]-a[1]);reject=False
  for q in keep:
   b=np.array(q['box_px']);inter=np.maximum(0,np.minimum(a[2:],b[2:])-np.maximum(a[:2],b[:2])).prod();ar2=(b[2]-b[0])*(b[3]-b[1])
   if inter/max(1,min(area,ar2))>.55:reject=True;break
  if not reject:keep.append(p)
 out=Image.fromarray(im[...,::-1]);dr=ImageDraw.Draw(out)
 for k,p in enumerate(keep):dr.rectangle(tuple(p['box_px']),outline='red',width=2);dr.text(tuple(p['box_px'][:2]),str(k),font=font,fill='yellow',stroke_fill='black',stroke_width=1)
 out.save(P/(prefix+'_mser.jpg'));result.append(dict(**e,opening_proposals=keep))
(P/'mser_opening_proposals.json').write_text(json.dumps(dict(entries=result,status='automatic multi-threshold source components, visual review pending'),indent=2));print('MSER_PROPOSALS',sum(len(e['opening_proposals']) for e in result))
