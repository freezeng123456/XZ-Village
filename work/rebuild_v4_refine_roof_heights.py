"""Evaluate source texture against adjacent calibrated views for every flat roof."""
import os,json,cv2,numpy as np
from rebuild_v4_arch_geometry import *
from rebuild_v4_photometric_roof import solve
P=OUT;ann=json.loads((P/'census_masks/manifest.json').read_text())['entries'];fits={b['id']:b for b in json.loads((P/'census_fitted.json').read_text())['entries']};r=np.load(P/'village_raster.npz');lo=r['lo'];res=float(r['res']);dtm=r['ground101'];selection=set(filter(None,os.getenv('ROOF_IDS','').split(',')));results=[]
for e in ann:
 if selection and e['id'] not in selection:continue
 if e['roof_type']!='flat':continue
 mask=cv2.imread(e['mask_path'],0);box=np.array(e['search_box_px']);bb=np.zeros_like(mask);cv2.rectangle(bb,tuple(np.maximum(box[:2],0)),tuple(np.minimum(box[2:],[2399,1349])),255,-1);mask=cv2.bitwise_and(mask,bb);b=fits.get(e['id'])
 if b:
  base=b['base_height'];hint=b['roof_edge_height'];prior=hint if b['dense_surface_points']>100 and (e['floor_count'] is None or hint-base>2.5*e['floor_count']) else None
 else:
  q=intersect_z([box.reshape(2,2).mean(0)],e['source_image'],3)[0];ij=np.floor((q[:2]-lo)/res).astype(int);base=float(dtm[np.clip(ij[1],0,dtm.shape[0]-1),np.clip(ij[0],0,dtm.shape[1]-1)]);hint=None;prior=None
 result=solve(e['source_image'],mask,base,prior);result.update(id=e['id'],source_image=e['source_image'],dense_edge=hint,base=base);results.append(result);print(e['id'],'z',round(result.get('z',0),2),'DENSE',round(hint or 0,2),'score',round(result.get('score',0),3),'prom',round(result.get('prominence_over_1unit',0),3),flush=True)
 if len(results)%20==0:(P/'census_photometric_heights.partial.json').write_text(json.dumps(results,indent=2))
(P/os.getenv('ROOF_HEIGHT_OUT','census_photometric_heights.json')).write_text(json.dumps(results,indent=2));print('DONE',len(results),flush=True)
