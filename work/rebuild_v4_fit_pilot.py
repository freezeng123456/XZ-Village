"""Fit the annotated mixed block to final dense geometry and fixed cameras."""
import json,sys
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import gaussian_filter1d
from rebuild_v4_arch_geometry import *
from rebuild_v4_orthogonal_fit import orthogonal_outline
p=np.load(OUT/'surface_points.npz');xyz=p['xyz'];normal=p['normal'];color=p['rgb'];print('loaded',len(xyz),flush=True)
rast=np.load(OUT/'village_raster.npz');lo=rast['lo'];res=float(rast['res']);dtm=rast['dtm'];H,W=dtm.shape
name='frame_044.00.jpg';im,cam=camera(name);w=world(xyz);camxyz=w@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation;uv=cam.img_from_cam(camxyz);dep=camxyz[:,2]*S;ij=np.round(uv*.5).astype(int);ok=(dep>0)&(ij[:,0]>=0)&(ij[:,0]<1200)&(ij[:,1]>=0)&(ij[:,1]<675);zbuf=np.full((675,1200),np.inf,np.float32);np.minimum.at(zbuf,(ij[ok,1],ij[ok,0]),dep[ok]);visible=np.zeros(len(xyz),bool);visible[ok]=dep[ok]<zbuf[ij[ok,1],ij[ok,0]]+.45
uvint=np.round(uv).astype(int);onframe=(uvint[:,0]>=0)&(uvint[:,0]<2400)&(uvint[:,1]>=0)&(uvint[:,1]<1350)&visible
obs=json.loads((OUT/'pilot_source_annotations.json').read_text())['entries'];initial=json.loads((OUT/'initial_roof_fits.json').read_text());results=[]
for b in obs:
 poly=np.array(b['roof_polygon_px'],np.int32);mask=np.zeros((1350,2400),np.uint8);cv2.fillPoly(mask,[poly],1);mask=cv2.erode(mask,np.ones((5,5),np.uint8));ids=np.flatnonzero(onframe);ids=ids[mask[uvint[ids,1],uvint[ids,0]]>0];ids=ids[np.abs(normal[ids,2])>(.45 if b['roof_type']=='hip' else .84)]
 sparse=sparse_inside(name,poly)
 if len(sparse)>=3:
  sz=float(np.median(sparse[:,2]));ids=ids[abs(xyz[ids,2]-sz)<(4 if b['roof_type']=='hip' else 2.0)]
 if len(ids)<10:print('INSUFFICIENT',b['id'],len(ids),flush=True);continue
 zz=xyz[ids,2];bins=np.arange(np.percentile(zz,2)-.5,np.percentile(zz,98)+.5,.1);hist,edges=np.histogram(zz,bins);smooth=gaussian_filter1d(hist.astype(float),1.5);peak=(edges[:-1]+edges[1:])[np.argmax(smooth)]/2;sel=ids[abs(zz-peak)<.25];deck=float(np.median(xyz[sel,2]));fitz=deck+.32
 if b['id']=='P001':q=np.array(initial[b['id']]['corners']);fit=initial[b['id']]['fit'];fitz=float(q[0,2]);deck=fitz-.38
 else:
  if b['roof_type']=='hip':fitz=float(np.percentile(zz,8))-.12
  if b['roof_type']=='metal':fitz=float(np.median(zz))
  q,fit=orthogonal_outline(poly,name,fitz)
 if b['id']=='P002':
  correction=json.loads((OUT/'gray_eight_corner_trial.json').read_text());q=np.array(correction['q']);fit=correction['fit'];fitz=float(q[0,2]);b['accepted_eight_corner_source']='frame_256.00.jpg';b['accepted_eight_corner_pixels']=correction['return_outline'];b['outline_review']='Eight source-visible corners, confirmed against frame 44; front and rear recesses retained.'
 ctr=q[:,:2].mean(0);ci=np.floor((ctr-lo)/res).astype(int);ground=float(dtm[np.clip(ci[1],0,H-1),np.clip(ci[0],0,W-1)])
 # Interior DTM can retain low roofs. Query a 6 metre ring as an additional diagnostic.
 from shapely.geometry import Polygon,Point
 footprint=Polygon(q[:,:2]);minx,miny,maxx,maxy=footprint.buffer(6).bounds;x0,y0=np.floor((np.array([minx,miny])-lo)/res).astype(int);x1,y1=np.ceil((np.array([maxx,maxy])-lo)/res).astype(int);sur=dtm[max(0,y0):min(H,y1+1),max(0,x0):min(W,x1+1)];gstats=np.percentile(sur,[10,50,90]).tolist();ground=min(ground,gstats[1])
 result=dict(**b,footprint_world=q[:,:2].tolist(),roof_edge_height=fitz,observed_roof_surface_height=deck,base_height=ground,dense_surface_points=len(ids),roof_plane_support=len(sel),roof_z_percentiles=np.percentile(zz,[5,25,50,75,95]).tolist(),roof_color=np.median(color[sel],axis=0).astype(int).tolist(),fit=fit,ground_status='morphological ground estimate; visible facade contact review pending',ground_neighborhood_quantiles=gstats,completion_status='geometry fit proposal; neutral multiview review pending')
 if b['roof_type']=='hip':result['ridge_height']=float(np.percentile(zz,94))
 results.append(result);print(b['id'],'z',round(fitz,2),'ground',round(ground,2),'surface',len(ids),'fit',round(fit['rms_px'],2),flush=True)
(OUT/'pilot_fitted.json').write_text(json.dumps(dict(entries=results,status='fit proposal, not accepted pilot'),indent=2,ensure_ascii=False))
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',19)
for sec in [44,256,28,64]:
 name=f'frame_{sec:06.2f}.jpg';image=Image.open(ROOT/'sfm/images'/name);draw=ImageDraw.Draw(image)
 for i,b in enumerate(results):
  q=np.column_stack([b['footprint_world'],np.full(len(b['footprint_world']),b['roof_edge_height'])]);v=project(q,name);color=tuple(int(x) for x in cv2.cvtColor(np.uint8([[[i*17%180,210,255]]]),cv2.COLOR_HSV2RGB)[0,0])
  if not np.isfinite(v).all() or (v[:,0].max()<0) or (v[:,0].min()>2400) or (v[:,1].max()<0) or (v[:,1].min()>1350):continue
  draw.line([tuple(vv) for vv in np.r_[v,v[:1]]],fill=color,width=3);draw.text(tuple(v.mean(0)),b['id'],fill=color,font=font,stroke_width=1,stroke_fill='black')
 image.save(OUT/f'pilot_projection_{sec:03}.jpg',quality=95)
