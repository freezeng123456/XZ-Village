"""Make source-camera evidence cards for incomplete and sparsely supported roofs."""
import json,cv2,numpy as np,os
from PIL import Image,ImageDraw,ImageFont
from rebuild_v4_arch_geometry import *
P=OUT;dest=P/'alternate_views';dest.mkdir(exist_ok=True);d=json.loads((P/'village_mesh_input.json').read_text());geom={b['id']:b for b in d['entries']};raw={b['id']:b for b in json.loads((P/'census_fitted.json').read_text())['entries']};ann={b['id']:b for b in json.loads((P/'census_box_annotations.json').read_text())['entries']};photo={b['id']:b for b in json.loads((P/'census_photometric_heights.json').read_text())};r=np.load(P/'village_raster.npz');ground=r['ground101'];lo=r['lo'];res=float(r['res']);ids=[x['id'] for x in d['unresolved']]+['V0069','V0072','V0201','V0236','V0335','V0348','V0366','V0367','V0486','V0504','V0511','V0513'];ids=list(dict.fromkeys(ids));manifest=[];font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',17)
ids=os.getenv('ALT_IDS',','.join(ids)).split(',')
for bid in ids:
 a=ann[bid];b=geom.get(bid,raw.get(bid));poly=None
 if b:
  xy=np.array(b['footprint_world']);q=np.r_[xy.mean(0),b['roof_edge_height']];poly=np.column_stack([xy,np.full(len(xy),q[2])])
 else:
  ph=photo.get(bid,{});z=ph.get('z',10);z=z if ph.get('score',0)>.70 else 12;box=np.array(a['search_box_px']).reshape(2,2);q=intersect_z([box.mean(0)],a['source_image'],z)[0]
 cand=[]
 for name,im in IMS.items():
  sec=float(name[6:-4]);C=local(im.projection_center());ray=C-q;dist=np.linalg.norm(ray);cos=ray[2]/dist
  if cos<.19 or dist<10 or dist>450:continue
  uv=project(np.array([q]),name)[0]
  if not np.isfinite(uv).all() or not(0<uv[0]<2400 and 0<uv[1]<1350):continue
  score=cos/dist**2;region='return' if sec>200 else 'outbound';cand.append((score,name,uv,region,dist))
 cand.sort(reverse=True,key=lambda t:t[0]);chosen=[]
 for item in cand:
  if len(chosen)>=2:break
  if chosen and item[3]==chosen[0][3] and abs(float(item[1][6:-4])-float(chosen[0][1][6:-4]))<10:continue
  chosen.append(item)
 card=Image.new('RGB',(1000,560),'#222');draw=ImageDraw.Draw(card);draw.text((10,5),bid+' | original '+a['source_image']+' | estimated roof center',font=font,fill='white');record=dict(id=bid,estimated_center=q.tolist(),views=[])
 for j,(_,name,uv,region,dist) in enumerate(chosen):
  image=Image.open(ROOT/'sfm/images'/name);cx,cy=uv;bb=[int(cx)-210,int(cy)-210,int(cx)+210,int(cy)+210];tile=image.crop(bb).resize((480,480));td=ImageDraw.Draw(tile)
  if poly is not None:
   pp=(project(poly,name)-bb[:2])*480/420;td.line([tuple(x) for x in np.r_[pp,pp[:1]]],fill='cyan',width=2)
  td.ellipse((233,233,247,247),outline='red',width=2);draw.text((j*500+10,32),name+f' crop {bb[0]},{bb[1]}',font=font,fill='white');card.paste(tile,(j*500+10,62));record['views'].append(dict(image=name,crop=bb,center_pixel=uv.tolist(),distance=dist))
 card.save(dest/f'{bid}.jpg',quality=95);manifest.append(record);print('CARD',bid,[x[1] for x in chosen],flush=True)
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
