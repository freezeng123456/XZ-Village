"""Assemble source-specific editable village geometry and evidence relationships.
No rejected V3 inventory, coordinates, materials or profiles are loaded.
"""
import json,numpy as np,cv2,copy,pycolmap as pc
from pathlib import Path
from shapely.geometry import Polygon
from rebuild_v4_arch_geometry import *
from rebuild_v4_plan_fit import footprint
P=OUT;source=json.loads((P/'census_fitted.json').read_text());fits={b['id']:b for b in source['entries']};ann={b['id']:b for b in json.loads((P/'census_masks/manifest.json').read_text())['entries']};photo={b['id']:b for b in json.loads((P/'census_photometric_heights.json').read_text())};relations=json.loads((P/'census_relationships.json').read_text());r=np.load(P/'village_raster.npz');lo=r['lo'];res=float(r['res']);ground=r['ground101'];pilot=json.loads((P/'pilot_mesh_input.json').read_text());results=[];changes=[];unresolved=[];images={}
for bid,a in ann.items():
 b=copy.deepcopy(fits.get(bid));ph=photo.get(bid,{});conf=ph.get('score',0)>.80 and ph.get('prominence_over_1unit',0)>.045;mask=cv2.imread(a['mask_path'],0);bbox=np.array(a['search_box_px']);rect=np.zeros_like(mask);cv2.rectangle(rect,tuple(np.maximum(bbox[:2],0)),tuple(np.minimum(bbox[2:],[2399,1349])),255,-1);mask=cv2.bitwise_and(mask,rect);ids=np.flatnonzero(mask.ravel());pix=np.column_stack([ids%2400,ids//2400]);z=ph.get('z')
 if b is None:
  if not conf or a['partial_image_boundary']:
   unresolved.append(dict(id=bid,reason='no reliable complete roof geometry yet',photometric_score=ph.get('score'),boundary=a['partial_image_boundary']));continue
  q=intersect_z(pix[::max(1,len(pix)//12000)],a['source_image'],z);xy,fit=footprint(q);b={k:v for k,v in a.items() if k not in ['polygon_px','mask_path']};b.update(name=a['note'],footprint_world=xy.tolist(),fit=fit,roof_edge_height=z,observed_roof_surface_height=z-.30,ridge_height=z,base_height=ph['base'],dense_surface_points=0,roof_color=[190,189,181],geometry_method='fixed-camera image-plane silhouette and photometric height',completion_status='recovered geometry proposal; source review pending');changes.append(dict(id=bid,action='recovered missing flat roof from adjacent photos',score=ph['score'],prominence=ph['prominence_over_1unit']))
 elif a['roof_type']=='flat' and conf:
  q=intersect_z(pix[::max(1,len(pix)//12000)],a['source_image'],z);xy,fit=footprint(q);oldarea=Polygon(b['footprint_world']).area;newarea=Polygon(xy).area;dz=abs(z-b['roof_edge_height']);weak=b['dense_surface_points']<65;substantially_incomplete=oldarea<newarea*.65
  if newarea>3 and newarea<600 and ((weak and not a['partial_image_boundary']) or (substantially_incomplete and ph['score']>.86 and ph['prominence_over_1unit']>.06) or (dz>.9 and ph['score']>.90 and ph['prominence_over_1unit']>.09)):
   changes.append(dict(id=bid,action='replace incomplete dense outline with image-plane outline',dense_area=oldarea,new_area=newarea,dense_height=b['roof_edge_height'],photo_height=z,score=ph['score']));b.update(footprint_world=xy.tolist(),fit=fit,roof_edge_height=z,observed_roof_surface_height=z-.30,geometry_method='camera-fixed source silhouette with adjacent-view roof-height match')
  elif dz<.70 and ph['score']>.86:
   b['roof_edge_height']=(b['roof_edge_height']+z)*.5;b['height_refinement']='mean of dense roof edge and consistent adjacent-view photometric edge'
 b['primary_source_image']=a['source_image'];b['photometric_height_audit']={k:ph[k] for k in ['z','score','prominence_over_1unit','neighbors'] if k in ph};b['source_ids']=[bid];b['source_role']='main_or_wing_pending';b['source_partial']=a['partial_image_boundary'];name=a['note'].lower()
 if 'canopy' in name or 'shade' in name or 'awning' in name or 'shelter' in name:b['source_role']='canopy'
 if bid in relations['roof_rooms']:b['source_role']='roof_room'
 if bid in relations['parent_relations']:b['parent_id']=relations['parent_relations'][bid];b['source_role']='wing' if b['source_role']=='main_or_wing_pending' else b['source_role']
 if bid in relations['special_forms']:b['special_form']=relations['special_forms'][bid]
 if bid in relations['roof_patches']:b['source_role']='roof_patch';b['parent_id']=relations['roof_patches'][bid]
 # Preliminary box floor hints were not full facade counts. Height supplies a neutral initial count.
 h=b['roof_edge_height']-b['base_height'];b['preliminary_floor_hint']=a['floor_count'];b['floor_count']=1 if a['roof_type'] in ['gable','hip_metal'] or b['source_role'] in ['canopy','roof_room'] else max(1,min(6,int(round(h/4.1))));b['floor_status']='source-height initial estimate; facade row count still to be checked'
 if bid in ['V0480','V0481']:b['floor_count']=4;b['floor_status']='four facade levels visually confirmed in source 90'
 if bid=='V0482':b['floor_count']=3;b['floor_status']='three exposed concrete levels visually confirmed in source 90'
 if bid=='V0483':b['floor_count']=3;b['floor_status']='three facade levels visually confirmed in source 90'
 if bid=='V0484':b['floor_count']=4;b['floor_status']='four facade levels visually confirmed in source 90'
 if bid=='V0485':b['floor_count']=3;b['floor_status']='three facade levels visually confirmed in source 90'
 if bid=='V0452':b['floor_count']=5
 if a['source_image'] not in images:images[a['source_image']]=cv2.imread(str(ROOT/'sfm/images'/a['source_image']))[...,::-1]
 if len(pix)>10:
  pixels=images[a['source_image']][pix[:,1],pix[:,0]];b['source_roof_rgb']=np.median(pixels,axis=0).astype(int).tolist()
 results.append(b)
lookup={b['id']:b for b in pilot['entries']+results};removed=[]
for alias,target in relations['manual_aliases'].items():
 if alias not in lookup or target not in lookup:continue
 lookup[target].setdefault('source_ids',[target]).append(alias);removed.append(dict(id=alias,alias_of=target,reason='cross-view source identity and plan-overlap adjudication'))
for alias,target in relations['roof_patches'].items():
 if alias not in lookup or target not in lookup:continue
 lookup[target].setdefault('roof_patch_sources',[]).append(alias);removed.append(dict(id=alias,patch_of=target,reason='visible roof repair material patch, not an independent body'))
removeids={r['id'] for r in removed};results=[b for b in results if b['id'] not in removeids]
for b in results:
 if b['source_role']=='roof_room' and b.get('parent_id') in lookup:
  par=lookup[b['parent_id']];b['base_height']=par['roof_edge_height']-.33;b['floor_count']=1
  if b['roof_edge_height']<b['base_height']+.5:b['source_role']='roof_fixture_or_room_ambiguous';b['base_height']=min(b['roof_edge_height']-.7,par['roof_edge_height']-.33)
 b.setdefault('geometry_method','source mask selected dense roof-plane footprint')
allb=pilot['entries']+results
# Actual terrain is a mesh from the broad ground estimate; its material is created procedurally.
xs=np.arange(-680,170,4);ys=np.arange(-310,600,4);gx,gy=np.meshgrid(xs,ys);ii=np.floor((gx-lo[0])/res).astype(int);jj=np.floor((gy-lo[1])/res).astype(int);gz=ground[np.clip(jj,0,ground.shape[0]-1),np.clip(ii,0,ground.shape[1]-1)];verts=np.column_stack([gx.ravel(),gy.ravel(),gz.ravel()]);faces=[]
for j in range(len(ys)-1):
 for i in range(len(xs)-1):
  k=j*len(xs)+i;faces.append([k,k+1,k+len(xs)+1,k+len(xs)])
rec=pc.Reconstruction(ROOT/'village_surface/sparse');cams=[]
for sec in [0,24,44,64,90,120,256,262]:
 name=f'frame_{sec:06.2f}.jpg';im=next(im for im in rec.images.values() if im.name==name);cam=rec.cameras[im.camera_id];cams.append(dict(name=f'source_{sec:03}',image=name,R=(im.cam_from_world().rotation.matrix()@A.T).tolist(),center=local(im.projection_center()).tolist(),width=cam.width,height=cam.height,params=cam.params.tolist()))
d=dict(entries=allb,cameras=cams,ground_mesh=dict(vertices=verts.tolist(),faces=faces),status='full village architecture input, source and facade verification incomplete',unresolved=unresolved,removed_or_grouped=removed,geometry_changes=changes)
(P/'village_mesh_input.json').write_text(json.dumps(d,ensure_ascii=False));(P/'village_geometry_decisions.json').write_text(json.dumps(dict(entries=len(allb),changes=changes,removed=removed,unresolved=unresolved),indent=2,ensure_ascii=False));print('READY',len(allb),'CHANGES',len(changes),'REMOVED',len(removed),'UNRESOLVED',len(unresolved),flush=True)
# Source roof outlines make geometric coverage and errors reviewable before adding facades.
for sec in [0,44,64,90,120,256,262]:
 name=f'frame_{sec:06.2f}.jpg';im=cv2.imread(str(ROOT/'sfm/images'/name))
 for i,b in enumerate(allb):
  xy=np.array(b['footprint_world']);v=project(np.column_stack([xy,np.full(len(xy),b['roof_edge_height'])]),name)
  if not np.isfinite(v).all() or (v[:,0].max()<0) or (v[:,0].min()>2400) or (v[:,1].max()<0) or (v[:,1].min()>1350):continue
  v=np.round(v).astype(np.int32);c=tuple(int(t) for t in cv2.cvtColor(np.uint8([[[i*43%180,210,250]]]),cv2.COLOR_HSV2BGR)[0,0]);cv2.polylines(im,[v],True,c,2);ctr=v.mean(0).astype(int);cv2.putText(im,b['id'],tuple(ctr),cv2.FONT_HERSHEY_SIMPLEX,.42,(0,0,0),3);cv2.putText(im,b['id'],tuple(ctr),cv2.FONT_HERSHEY_SIMPLEX,.42,c,1)
 cv2.imwrite(str(P/f'village_geometry_{sec:03}.jpg'),im,[cv2.IMWRITE_JPEG_QUALITY,94])
