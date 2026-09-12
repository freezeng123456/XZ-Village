"""Estimate coherent surface colours without baking misplaced image fragments."""
import json,cv2,numpy as np
from pathlib import Path
root=Path.cwd();data=json.loads((root/'work/buildings/visibility/architecture_visibility.json').read_text());poses=json.loads((root/'work/buildings/visibility/poses.json').read_text());cache={};result={}
def colour(info):
 ts=str(info['source_time'])
 if ts not in cache:cache[ts]=cv2.resize(cv2.imread(str(root/poses[ts]['source'])),(1600,900))[:,:,::-1]
 x,y,w,h=info['mask_bounds_px'];mask=cv2.imread(str(root/info['mask']),0);pix=cache[ts][y:y+h,x:x+w][mask>128]
 if len(pix)<20:return None
 lum=pix@np.array([.2126,.7152,.0722]);keep=(lum>np.percentile(lum,40))&(lum<np.percentile(lum,92));pix=pix[keep]
 if len(pix)<10:return None
 bins=(pix//24).astype(int);key=bins[:,0]*121+bins[:,1]*11+bins[:,2];values,counts=np.unique(key,return_counts=True);chosen=values[counts.argmax()];rgb=np.median(pix[key==chosen],axis=0)/255;rgb=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);rgb=np.clip(rgb*1.4,.045,.8);return rgb.tolist()
for b in data['buildings']:
 faces={str(f['edge']):dict(rgb=colour(f),pixels=f['source_visible_pixels']) for f in b.get('visible_facades',[])};usable=[f for f in faces.values() if f['rgb']];wall=max(usable,key=lambda f:f['pixels'])['rgb'] if usable else [.5,.51,.46]
 if b.get('public_hall'):wall=[.46,.065,.04]
 if b.get('finish_style')=='exposed_brick':wall=[.43,.22,.12]
 result[b['id']]=dict(wall=wall,faces=faces,roof=colour(b['roof_texture']) if b.get('roof_texture') else None,type=b['type'],finish_style=b.get('finish_style'),public_hall=b.get('public_hall',False))
(root/'work/buildings/surface_finishes.json').write_text(json.dumps(result,indent=2));print('Sampled surface colours for',len(result),'units')
