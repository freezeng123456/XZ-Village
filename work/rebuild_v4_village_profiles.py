"""Source-visible opening proposals and per-face finishes, with explicit provenance.
Detection uses only rectified video observations and their occlusion masks. It never
tiles a common facade over the village. Pilot hand measurements take precedence.
"""
import json,cv2,numpy as np,os
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path('work/rebuild4/architecture');D=P/'village_facades';d=json.loads((P/'village_mesh_input.json').read_text());faces=json.loads((D/'manifest.json').read_text())['entries'];pilot={p['id']:p for p in json.loads((P/'pilot_profiles.json').read_text())['entries']};by={};out=[];audit=[];preview=D/'opening_reviews';preview.mkdir(exist_ok=True);font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',14)
for f in faces:by.setdefault(f['building_id'],[]).append(f)
def detect(im,vis,f,b):
 hh,ww=im.shape[:2];sx=ww/f['length'];sy=hh/f['height'];gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV);valid=cv2.erode(vis,np.ones((3,3),np.uint8))>0;valid[:max(2,int(sy*.22))]=False;valid[:,:max(2,int(sx*.10))]=False;valid[:,-max(2,int(sx*.10)):]=False
 if valid.sum()<100:return [],[],[.74,.74,.70],'plaster',[]
 vals=gray[valid];walllevel=float(np.percentile(vals,74));wallsel=valid&(gray>np.percentile(vals,55))&(gray<np.percentile(vals,91));wallrgb=np.median(im[wallsel][:,::-1],axis=0)/255 if wallsel.any() else np.array([.74,.74,.70]);color=np.clip(wallrgb,.24,.93);warm=color[0]-color[2]>.12 and color[0]>color[1]*1.10
 style='brick' if warm and np.mean(color)<.64 else ('ceramic' if np.mean(color)>.64 and b['roof_type'] not in ['gable','hip_metal'] else 'plaster')
 if f['visible_fraction']<.35 or f['camera_cos']<.20:return [],[],color.tolist(),style,[]
 kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(max(9,int(sx*3.2))|1,max(9,int(sy*3.0))|1));shade=cv2.morphologyEx(gray,cv2.MORPH_BLACKHAT,kernel).astype(float);dark=(gray<min(walllevel-25,walllevel*.72))&(shade>18);green=(hsv[:,:,0]>30)&(hsv[:,:,0]<100)&(hsv[:,:,1]>80)&(gray<walllevel*.91)&(shade>12);fg=((dark|green)&valid).astype(np.uint8)*255
 fg=cv2.morphologyEx(fg,cv2.MORPH_CLOSE,np.ones((max(2,int(sy*.095)),max(2,int(sx*.10))),np.uint8));cnts,_=cv2.findContours(fg,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);candidates=[]
 for c in cnts:
  x,y,w,h=cv2.boundingRect(c);wu,hu=w/sx,h/sy;aspect=wu/hu;area=cv2.contourArea(c);fill=area/max(1,w*h)
  if not(.52<wu<min(9,f['length']*.95) and .58<hu<min(3.8,f['height']*.7) and .21<aspect<5.0 and fill>.27):continue
  patchvis=valid[y:y+h,x:x+w].mean();inside=float(gray[y:y+h,x:x+w].mean());maskfill=float((fg[y:y+h,x:x+w]>0).mean())
  if patchvis<.70 or inside>walllevel-18 or maskfill<.31:continue
  border=[];pad=max(2,int(min(sx,sy)*.10));x0=max(0,x-pad);x1=min(ww,x+w+pad);y0=max(0,y-pad);y1=min(hh,y+h+pad)
  for strip in [gray[y0:y,x0:x1],gray[y+h:y1,x0:x1],gray[y:y+h,x0:x],gray[y:y+h,x+w:x1]]:
   if strip.size:border.append(float(np.mean(strip)))
  contrast=np.mean(border)-inside if border else 0
  if contrast<6:continue
  confidence=float(np.clip(.30+fill*.35+contrast/200+patchvis*.15,0,1));kind='window'
  if (y+h)/hh>.92 and hu>1.6:kind='door'
  if hu<.65 and wu<.85:kind='vent'
  candidates.append(dict(box=[x/ww,y/hh,(x+w)/ww,(y+h)/hh],kind=kind,inferred=False,confidence=confidence,source_image=f['image'],source_method='rectified dark or colored opening component; geometry and visibility filtered',size=[wu,hu],mean_rgb=(np.mean(im[y:y+h,x:x+w].reshape(-1,3)[:,::-1],axis=0)/255).tolist()))
 candidates.sort(key=lambda c:c['confidence'],reverse=True);candidates=candidates[:max(5,b['floor_count']*8)];ops=[];bal=[];glazing=[]
 for c in candidates:
  x0,y0,x1,y1=c['box'];wu,hu=c['size'];lvl=int(np.clip(np.round(((1-(y0+y1)/2)*b['floor_count'])-.5),0,b['floor_count']-1));expected=(lvl+.5)/b['floor_count'];center=1-(y0+y1)/2
  if wu>3.1 and hu>1.55 and abs(center-expected)<.15 and b['roof_type']=='flat' and lvl>0 and c['mean_rgb'][1]<.43:
   bal.append(dict(x0=x0,x1=x1,floors=[lvl],depth=min(1.2,wu*.22),rail='metal',inferred=False,source_method=c['source_method'],confidence=c['confidence']));continue
  glazing.append(c['mean_rgb']);ops.append(c)
 return ops,bal,color.tolist(),style,glazing
for b in d['entries']:
 bid=b['id']
 if bid in pilot:out.append(pilot[bid]);continue
 typ=b['roof_type'];rgb=np.array(b.get('source_roof_rgb',b.get('roof_color',[175,171,156])))/255;roofcolor=np.clip(rgb,.13,.94).tolist();p=dict(id=bid,color=[.73,.73,.69],style='plaster',roof_color=roofcolor,wall_age=.46,roof_age=.58,glazing_color=[.19,.26,.23],faces={},equipment=[],roof_patches=[],provenance='per-face video rectification; machine proposals await visual adjudication');colors=[];glasses=[];visible=0
 for f in by.get(bid,[]):
  key=f'{bid}_f{f["face"]:02}';im=cv2.imread(str(D/(key+'.jpg')));vis=cv2.imread(str(D/(key+'_visible.png')),0);ops,bal,col,style,glaz=detect(im,vis,f,b);p['faces'][str(f['face'])]=dict(openings=ops,balconies=bal,equipment=[],color=col,style=style,source_image=f['image'],visible_fraction=f['visible_fraction'],annotation_status='automatic source-derived proposal');colors.append((f['visible_fraction']*f['length'],col,style));glasses.extend(glaz);visible+=int(f['visible_fraction']>.4)
  pic=Image.fromarray(im[:,:,::-1]);draw=ImageDraw.Draw(pic)
  for op in ops:
   x0,y0,x1,y1=np.array(op['box'])*[im.shape[1],im.shape[0],im.shape[1],im.shape[0]];draw.rectangle([x0,y0,x1,y1],outline='#31ffae',width=2)
  for log in bal:
   for lv in log['floors']:draw.rectangle([log['x0']*im.shape[1],(1-(lv+1)/b['floor_count'])*im.shape[0],log['x1']*im.shape[1],(1-lv/b['floor_count'])*im.shape[0]],outline='#ffa536',width=2)
  pic.thumbnail((500,450));card=Image.new('RGB',(max(290,pic.width),pic.height+42),'#20252b');dr=ImageDraw.Draw(card);dr.text((5,3),key+f' v={f["visible_fraction"]:.2f} / '+f['image'],font=font,fill='white');dr.text((5,21),f'{len(ops)} openings; {len(bal)} loggias; '+style,font=font,fill='white');card.paste(pic,(0,42));card.save(preview/(key+'.jpg'),quality=90)
 if colors:
  best=max(colors,key=lambda v:v[0]);p['color']=best[1];p['style']=best[2]
  for ff in p['faces'].values():
   if ff['visible_fraction']<.35:ff['color']=p['color'];ff['style']=p['style']
 if glasses:p['glazing_color']=np.clip(np.median(glasses,axis=0),.08,.45).tolist()
 if typ in ['gable','hip_metal']:p['wall_age']=.65;p['roof_age']=.76
 if b.get('source_role')=='canopy':p['style']='plaster'
 if b.get('special_form')=='exposed_concrete_frame':
  for f in p['faces'].values():f['concrete_frame']=True
 out.append(p);audit.append(dict(id=bid,faces=len(p['faces']),visible_faces=visible,openings=sum(len(f['openings']) for f in p['faces'].values()),loggias=sum(len(f['balconies']) for f in p['faces'].values())));print('PROFILE',audit[-1],flush=True)
(P/'village_profiles.json').write_text(json.dumps(dict(entries=out,status='source-derived opening proposals and manually reviewed pilot'),ensure_ascii=False,indent=2));(P/'village_profile_audit.json').write_text(json.dumps(audit,indent=2));print('DONE',len(out),'OPENINGS',sum(x['openings'] for x in audit),flush=True)
# Compact sheets show up to two highest-visibility faces per building for model review.
gallery=P/'facade_gallery';gallery.mkdir(exist_ok=True);items=[]
for b in d['entries']:
 if b['id'] in pilot:continue
 for f in sorted(by.get(b['id'],[]),key=lambda f:f['visible_fraction']*f['length'],reverse=True)[:2]:
  path=preview/f'{b["id"]}_f{f["face"]:02}.jpg'
  if path.exists():items.append(path)
for page in range((len(items)+23)//24):
 canvas=Image.new('RGB',(1600,1440),'#171a20')
 for i,path in enumerate(items[page*24:(page+1)*24]):
  im=Image.open(path);im.thumbnail((398,238));canvas.paste(im,(i%4*400,i//4*240))
 canvas.save(gallery/f'facades_{page:02}.jpg',quality=94)
