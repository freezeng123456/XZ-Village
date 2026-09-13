"""Recover incomplete roof extents from visually reviewed alternate source frames.
Photo crops are measurement references only. No photo enters the architectural scene.
"""
import json,cv2,numpy as np,os
from scipy.ndimage import gaussian_filter1d
from rebuild_v4_arch_geometry import *
from rebuild_v4_orthogonal_fit import orthogonal_outline
from rebuild_v4_photometric_roof import solve
P=OUT
# Card coordinates recorded against the archived 1000x560 source evidence cards.
rows=[]
def card(bid,sec,crop,polygon,view=0,floors=None,role=None,z=None,parent=None):
 pp=np.array(polygon,float);pp=(pp-[10+500*view,62])*420/480+crop
 rows.append(dict(id=bid,source_image=f'frame_{sec:06.2f}.jpg',polygon_px=pp.tolist(),floor_count=floors,source_role=role,height_override=z,parent_id=parent))
card('V0065',255,[583,970],[[151,339],[249,339],[272,220],[175,225]],floors=3)
card('V0068',254,[335,916],[[51,449],[212,438],[255,252],[60,267],[35,345],[82,347]],floors=3)
card('V0069',254,[214,911],[[214,309],[271,304],[279,332],[219,339]],floors=1,role='roof_room',z=15.00,parent='V0068')
card('V0072',253,[-50,833],[[67,329],[267,331],[306,224],[110,233]],floors=1,role='main_or_wing_pending',z=7.48)
card('V0234',238,[1531,993],[[754,282],[855,345],[830,353],[732,290]],view=1,floors=1,role='canopy')
card('V0236',254,[1457,906],[[233,280],[269,283],[268,296],[345,297],[347,279],[380,281],[382,311],[259,314],[255,355],[236,349]],floors=1,role='canopy',z=10.82)
card('V0319',236,[2006,808],[[261,289],[301,284],[375,313],[337,318]],floors=3)
card('V0335',28,[518,493],[[691,289],[727,236],[929,231],[899,312],[844,310],[842,282]],view=1,floors=3)
card('V0348',0,[-50,439],[[70,411],[224,413],[301,338],[157,333]],floors=4)
card('V0351',28,[518,493],[[562,384],[836,382],[856,329],[826,327],[847,284],[637,289],[613,344],[578,346]],view=1,floors=4)
card('V0351W1',26,[354,519],[[705,303],[719,284],[831,285],[799,321],[712,320],[721,306]],view=1,floors=2,role='wing',parent='V0351')
card('V0356',0,[-145,599],[[176,332],[263,332],[310,280],[176,274]],floors=3,z=17.39)
card('V0360',2,[199,684],[[741,290],[774,290],[754,325],[729,325]],view=1,floors=1,role='canopy')
card('V0366',24,[337,812],[[190,368],[282,365],[311,306],[219,309]],floors=1,role='canopy',z=None)
card('V0367',24,[808,791],[[47,422],[425,413],[424,270],[81,274]],floors=3,z=11.10)
card('V0464',90,[-9,221],[[242,299],[283,290],[310,301],[269,310]],floors=1,role='canopy')
card('V0485',90,[1510,859],[[212,258],[488,288],[464,183],[206,156]],floors=3,z=13.64)
card('V0486',90,[1510,859],[[207,344],[474,372],[480,415],[188,382]],floors=2,role='wing',z=9.86,parent='V0485')
card('V0504',128,[624,841],[[112,385],[231,425],[429,291],[307,254]],floors=4,z=25.53)
card('V0511',134,[1012,817],[[232,179],[312,189],[328,125],[255,116]],floors=2,role='wing')
card('V0513',110,[279,146],[[611,289],[780,273],[809,317],[631,336]],view=1,floors=4,z=24.35)
rows.append(dict(id='V0362',source_image='frame_000.00.jpg',polygon_px=[[720,955],[907,951],[889,1075],[833,1077],[832,1062],[699,1064]],floor_count=3,height_override=11.27))
rows.append(dict(id='V0501',source_image='frame_120.00.jpg',polygon_px=[[0,433],[53,433],[101,408],[0,408]],floor_count=3,base_override=35.0))
extra=P/'manual_recovery_extra.json'
if extra.exists():rows.extend(json.loads(extra.read_text()))
(P/'manual_recovery_annotations.json').write_text(json.dumps(rows,indent=2))
d=json.loads((P/'village_mesh_input.json').read_text());geom={b['id']:b for b in d['entries']};ann={a['id']:a for a in json.loads((P/'census_box_annotations.json').read_text())['entries']};rr=np.load(P/'village_raster.npz');ground=rr['ground101'];lo=rr['lo'];res=float(rr['res']);ss=np.load(P/'surface_points.npz');xyz=ss['xyz'][::2];normal=ss['normal'][::2];pw=world(xyz);viscache={};out=[]
def visible(name):
 if name not in viscache:
  im,cam=camera(name);q=pw@im.cam_from_world().rotation.matrix().T+im.cam_from_world().translation;uv=cam.img_from_cam(q);uv=np.round(np.nan_to_num(uv,nan=-1e5)).astype(int);z=q[:,2]*S;ok=(z>0)&(uv[:,0]>=0)&(uv[:,0]<2400)&(uv[:,1]>=0)&(uv[:,1]<1350);ij=uv//2;depth=np.full((675,1200),np.inf,np.float32);np.minimum.at(depth,(ij[ok,1],ij[ok,0]),z[ok]);ok[ok]=z[ok]<depth[ij[ok,1],ij[ok,0]]+.50;ids=np.flatnonzero(ok);viscache[name]=(ids,uv[ids])
 return viscache[name]
select=set(os.getenv('RECOVERY_IDS',','.join(r['id'] for r in rows)).split(','));oldfile=P/'manual_recovery_results.json';old={b['id']:b for b in json.loads(oldfile.read_text())} if oldfile.exists() else {}
for a in rows:
 bid=a['id']
 if bid not in select:
  if bid in old:out.append(old[bid])
  continue
 name=a['source_image'];poly=np.array(a['polygon_px']);mask=np.zeros((1350,2400),np.uint8);cv2.fillPoly(mask,[np.round(poly).astype(int)],255);ids,uv=visible(name);sel=ids[(mask[uv[:,1],uv[:,0]]>0)&(np.abs(normal[ids,2])>.80)];zz=xyz[sel,2];base=geom.get(bid,{}).get('base_height')
 if base is None:
  pp=xyz[sel,:2].mean(0) if len(sel) else intersect_z([poly.mean(0)],name,12)[0,:2];ii=np.floor((pp-lo)/res).astype(int);base=float(ground[np.clip(ii[1],0,ground.shape[0]-1),np.clip(ii[0],0,ground.shape[1]-1)])+.12
 base=a.get('base_override',base);zz=zz[zz>base+1]
 peak=None
 if len(zz)>8:
  edges=np.arange(np.percentile(zz,1)-.3,np.percentile(zz,99)+.6,.15);hist,_=np.histogram(zz,edges);peak=float((edges[:-1]+edges[1:])[np.argmax(gaussian_filter1d(hist.astype(float),2))]/2)
 z=a.get('height_override');ph={}
 if z is None:
  ph=solve(name,mask,base,peak if len(zz)>50 else None);z=ph.get('z',peak)
  if peak is not None and ph.get('score',0)<.75:z=peak+.3
 if z is None:print('FAILED',bid,flush=True);continue
 vv,fit=orthogonal_outline(poly,name,z);a.update(footprint_world=vv[:,:2].tolist(),roof_edge_height=z,base_height=base,dense_z_quantiles=np.percentile(zz,[5,50,95]).tolist() if len(zz) else [],dense_peak=peak,dense_points=len(zz),fit=fit,photometric_evidence=ph);out.append(a);oldfile.write_text(json.dumps(out+[v for k,v in old.items() if k not in {b['id'] for b in out}],indent=2));print(bid,'z',round(z,2),'base',round(base,2),'points',len(zz),'dense',peak,'photo',round(ph.get('score',0),3),'err',round(fit['rms_px'],2),flush=True)
oldfile.write_text(json.dumps(out,indent=2));print('DONE',len(out),flush=True)
