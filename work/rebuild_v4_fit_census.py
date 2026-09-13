"""Fit fresh image-located roof surfaces to final dense points and frozen cameras.
The result is a geometric proposal ledger; no source mask is a building count.
"""
import json,cv2,numpy as np
from pathlib import Path
from scipy.ndimage import gaussian_filter1d,binary_closing,binary_fill_holes,label
from scipy.optimize import minimize_scalar
from shapely.geometry import Polygon,box
from rebuild_v4_arch_geometry import *
P=OUT;d=np.load(P/'surface_points.npz');xyz=d['xyz'];normal=d['normal'];rgb=d['rgb'];rast=np.load(P/'village_raster.npz');ground=rast['ground101'];lo=rast['lo'];res=float(rast['res']);entries=json.loads((P/'census_masks/manifest.json').read_text())['entries'];results=[];fail=[]
print('POINTS',len(xyz),flush=True)
# A pixel owns its nearest observed surface; roof points behind other houses are excluded.
w=world(xyz);viscache={}
def visible(name):
 if name in viscache:return viscache[name]
 im,cam=camera(name);q=w@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation;uv=cam.img_from_cam(q);depth=q[:,2]*S;uv=np.nan_to_num(uv,nan=-1e5,posinf=-1e5,neginf=-1e5);ij=np.round(uv*.5).astype(int);ok=(depth>0)&(ij[:,0]>=0)&(ij[:,0]<1200)&(ij[:,1]>=0)&(ij[:,1]<675);z=np.full((675,1200),np.inf,np.float32);np.minimum.at(z,(ij[ok,1],ij[ok,0]),depth[ok]);keep=ok.copy();keep[ok]=depth[ok]<z[ij[ok,1],ij[ok,0]]+.45;uv=np.round(uv).astype(int);keep&=(uv[:,0]>=0)&(uv[:,0]<2400)&(uv[:,1]>=0)&(uv[:,1]<1350);ids=np.flatnonzero(keep);viscache[name]=(ids,uv[ids]);return ids,uv[ids]
from rebuild_v4_plan_fit import footprint
for e in entries:
 ids,uv=visible(e['source_image']);mask=cv2.imread(e['mask_path'],0);mask=cv2.erode(mask,np.ones((3,3),np.uint8));sel=ids[mask[uv[:,1],uv[:,0]]>0];bb=e['search_box_px'];vv=project(xyz[sel],e['source_image']);sel=sel[(vv[:,0]>bb[0]-3)&(vv[:,0]<bb[2]+3)&(vv[:,1]>bb[1]-3)&(vv[:,1]<bb[3]+3)];slope=e['roof_type'] in ['gable','hip','hip_metal','metal','solar'];sel=sel[np.abs(normal[sel,2])>(.55 if slope else .86)]
 if len(sel)<6:fail.append(dict(id=e['id'],reason='insufficient roof-normal visible support',points=len(sel)));continue
 zz=xyz[sel,2];xy=np.median(xyz[sel,:2],axis=0);ij=np.floor((xy-lo)/res).astype(int);base=float(ground[np.clip(ij[1],0,ground.shape[0]-1),np.clip(ij[0],0,ground.shape[1]-1)])+.12;sel=sel[xyz[sel,2]>base+1.2]
 if len(sel)<6:fail.append(dict(id=e['id'],reason='no roof sufficiently above terrain',points=len(sel)));continue
 zz=xyz[sel,2];bins=np.arange(np.percentile(zz,1)-.5,np.percentile(zz,99)+.6,.15);hist,edges=np.histogram(zz,bins);hist=gaussian_filter1d(hist.astype(float),2);peak=float((edges[:-1]+edges[1:])[np.argmax(hist)]/2);keep=abs(zz-peak)<(3.5 if slope else .65);sel=sel[keep]
 # Reject disconnected roof/ground islands within a broad mask.
 pp=xyz[sel];origin=pp[:,:2].min(0)-.6;pix=np.floor((pp[:,:2]-origin)/.3).astype(int);siz=pix.max(0)+3
 if np.prod(siz)>5e6:fail.append(dict(id=e['id'],reason='unbounded point spread'));continue
 gg=np.zeros(siz[::-1],np.uint8);gg[pix[:,1],pix[:,0]]=1;gg=cv2.dilate(gg,np.ones((5,5),np.uint8));n,ll,stats,_=cv2.connectedComponentsWithStats(gg);big=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]);sel=sel[ll[pix[:,1],pix[:,0]]==big]
 if len(sel)<6:fail.append(dict(id=e['id'],reason='sparse dominant roof cluster'));continue
 pp=xyz[sel];zz=pp[:,2];xy,fit=footprint(pp);area=Polygon(xy).area
 if area<1.5:fail.append(dict(id=e['id'],reason='tiny roof plane',area=area));continue
 qz=np.percentile(zz,[5,25,50,75,95]);deck=float(np.median(zz));edge=float(qz[0]-.08 if slope else deck+(.30 if e['roof_type']=='flat' else .08));ridge=float(qz[4]);floors=e['floor_count'] or max(1,min(6,int(round((edge-base-.4)/3.8))));result={k:v for k,v in e.items() if k not in ['polygon_px','mask_path']};plane=np.linalg.lstsq(np.column_stack([pp[:,:2],np.ones(len(pp))]),zz,rcond=None)[0];
 result.update(name=e['note'],footprint_world=xy.tolist(),roof_edge_height=edge,observed_roof_surface_height=deck,ridge_height=ridge,base_height=base,floor_count=floors,floor_status=e['floor_status'] if e['floor_count'] else 'provisional from measured roof-to-ground height; facade review pending',dense_surface_points=len(sel),roof_z_percentiles=qz.tolist(),roof_color=np.median(rgb[sel],axis=0).astype(int).tolist(),fit=fit,completion_status='dense geometry proposal; multiview roof and facade review pending');result['observed_surface_plane']=np.linalg.lstsq(np.column_stack([pp[:,:2],np.ones(len(pp))]),zz,rcond=None)[0].tolist();results.append(result)
 if len(results)%20==0:print('FITTED',len(results),'LATEST',e['id'],'FAIL',len(fail),flush=True)
(P/'census_fitted.json').write_text(json.dumps(dict(entries=results,unresolved=fail,status='proposals require per-source review and grouping; not accepted building count'),indent=2));print('DONE',len(results),'FAIL',fail,flush=True)
for sec in [256,44,0,64,90,120,262]:
 name=f'frame_{sec:06.2f}.jpg'
 if name not in IMS:continue
 image=cv2.imread(str(ROOT/'sfm/images'/name))
 for i,b in enumerate(results):
  xy=np.array(b['footprint_world']);v=project(np.column_stack([xy,np.full(len(xy),b['roof_edge_height'])]),name)
  if not np.isfinite(v).all() or (v[:,0].max()<0) or (v[:,0].min()>2400) or (v[:,1].max()<0) or (v[:,1].min()>1350):continue
  col=tuple(int(c) for c in cv2.cvtColor(np.uint8([[[i*41%180,210,255]]]),cv2.COLOR_HSV2BGR)[0,0]);v=np.round(v).astype(np.int32);cv2.polylines(image,[v],True,col,2);ctr=v.mean(0).astype(int);cv2.putText(image,b['id'],tuple(ctr),cv2.FONT_HERSHEY_SIMPLEX,.40,(0,0,0),3);cv2.putText(image,b['id'],tuple(ctr),cv2.FONT_HERSHEY_SIMPLEX,.40,col,1)
 cv2.imwrite(str(P/f'census_projection_{sec:03}.jpg'),image,[cv2.IMWRITE_JPEG_QUALITY,95])
