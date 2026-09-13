"""Propose connected roof planes for exhaustive visual census, not building counts.
Each proposal requires source-view review and grouping into main bodies/wings.
"""
import numpy as np,cv2,json,time
from pathlib import Path
from scipy import ndimage as nd
from PIL import Image,ImageDraw,ImageFont
P=Path('work/rebuild4/architecture');r=np.load(P/'village_raster.npz');step=2;res=float(r['res'])*step;lo=r['lo'];z=r['filled'][::step,::step];ground=r['ground101'][::step,::step];rgb=r['color'][::step,::step];coverage=r['coverage'][::step,::step];near=r['near'][::step,::step];H,W=z.shape;xx=lo[0]+(np.arange(W)+.5)*res;yy=lo[1]+(np.arange(H)+.5)*res
vegetation=(rgb[...,1]>rgb[...,0]*1.04)&(rgb[...,1]>rgb[...,2]*1.09);water=(z-ground<2.1);cand=near&(~vegetation)&(~water)&(z-ground<27)&(z<65);cand=nd.binary_closing(cand,iterations=1);cand&=near
# Signed height residual after fitting a small local plane measures seed reliability.
smooth=nd.gaussian_filter(z,1);lap=np.abs(nd.laplace(smooth));occupied=np.zeros((H,W),np.int32);seedmask=np.zeros_like(cand);seedmask[2::3,2::3]=True;sy,sx=np.where(seedmask&cand);score=lap[sy,sx]+1/(coverage[sy,sx].astype(float)+1)*.1;order=np.argsort(score);seeds=list(zip(sy[order],sx[order]));regions=[];start=time.time();RADIUS=65
print('CANDIDATE_PIXELS',cand.sum(),'SEEDS',len(seeds),flush=True)
for k,(j,i) in enumerate(seeds):
 if occupied[j,i] or not cand[j,i]:continue
 a,b=max(0,j-3),min(H,j+4);c,d=max(0,i-3),min(W,i+4);pat=cand[a:b,c:d]&(occupied[a:b,c:d]==0);py,px=np.where(pat)
 if len(px)<25:continue
 X=np.column_stack([(px+c-i)*res,(py+a-j)*res,np.ones(len(px))]);Z=z[py+a,px+c];coef=np.linalg.lstsq(X,Z,rcond=None)[0];err=Z-X@coef
 if np.median(abs(err))>.16 or np.percentile(abs(err),85)>.36 or np.linalg.norm(coef[:2])>.95:continue
 y0,y1=max(0,j-RADIUS),min(H,j+RADIUS+1);x0,x1=max(0,i-RADIUS),min(W,i+RADIUS+1);gx=(np.arange(x0,x1)-i)*res;gy=(np.arange(y0,y1)-j)*res;zz=z[y0:y1,x0:x1];active=cand[y0:y1,x0:x1]&(occupied[y0:y1,x0:x1]==0)
 chosen=None
 for it in range(3):
  pred=coef[0]*gx[None,:]+coef[1]*gy[:,None]+coef[2];allowed=(active&(abs(zz-pred)<.26)).astype(np.uint8);allowed=cv2.morphologyEx(allowed,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8));allowed&=active.astype(np.uint8)
  if allowed[j-y0,i-x0]==0:break
  flood=allowed.copy();_,_,_,rect=cv2.floodFill(flood,None,(int(i-x0),int(j-y0)),2);chosen=flood==2;py,px=np.where(chosen)
  if len(px)*res*res<7:chosen=None;break
  X=np.column_stack([gx[px],gy[py],np.ones(len(px))]);Z=zz[py,px];coef=np.linalg.lstsq(X,Z,rcond=None)[0]
 if chosen is None or np.linalg.norm(coef[:2])>1.0:continue
 py,px=np.where(chosen);area=len(px)*res*res
 if area<9:continue
 # Remove thin wall ledges and power-line fragments.
 coords=np.column_stack([px,py]).astype(np.float32);rect=cv2.minAreaRect(coords);ww,hh=rect[1]
 if min(ww,hh)*res<1.7:continue
 idx=len(regions)+1;occupied[y0:y1,x0:x1][chosen]=idx;contours,_=cv2.findContours(chosen.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cont=max(contours,key=cv2.contourArea);eps=.22/res;poly=cv2.approxPolyDP(cont,eps,True)[:,0,:].astype(float);poly[:,0]=lo[0]+(poly[:,0]+x0+.5)*res;poly[:,1]=lo[1]+(poly[:,1]+y0+.5)*res
 col=np.median(rgb[py+y0,px+x0],axis=0).astype(int);plane=[float(coef[0]),float(coef[1]),float(coef[2]-coef[0]*xx[i]-coef[1]*yy[j])];medh=float(np.median(z[py+y0,px+x0]-ground[py+y0,px+x0]));rms=float(np.sqrt(np.mean((X@coef-Z)**2)))
 regions.append(dict(proposal_id=f'R{idx:04}',index=idx,polygon=poly.tolist(),area_m2=area,plane=plane,color=col.tolist(),height_above_initial_ground=medh,rms_plane=rms,slope=float(np.linalg.norm(coef[:2])),pixel_count=len(px),status='unreviewed roof-plane proposal; not an independent building'))
 if idx%100==0:print('REGIONS',idx,'seeds',k,'elapsed',round(time.time()-start,1),flush=True)
np.savez_compressed(P/'roof_candidate_labels.npz',labels=occupied,res=res,lo=lo,candidate=cand)
(P/'roof_candidate_ledger.json').write_text(json.dumps(dict(status='UNREVIEWED plane proposals; no accepted building count',regions=regions,elapsed_seconds=time.time()-start),indent=2))
base=Image.fromarray(rgb[::-1]);draw=ImageDraw.Draw(base);font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',11)
for reg in regions:
 poly=np.array(reg['polygon']);ij=(poly-lo)/res;ij[:,1]=H-1-ij[:,1];color=tuple(int(x) for x in cv2.cvtColor(np.uint8([[[reg['index']*41%180,220,255]]]),cv2.COLOR_HSV2RGB)[0,0]);draw.line([tuple(q) for q in np.r_[ij,ij[:1]]],fill=color,width=1);c=ij.mean(0);draw.text(tuple(c),str(reg['index']),fill='white',font=font,stroke_width=1,stroke_fill='black')
base.save(P/'roof_candidates_overview.png');print('DONE',len(regions),'elapsed',time.time()-start,flush=True)
