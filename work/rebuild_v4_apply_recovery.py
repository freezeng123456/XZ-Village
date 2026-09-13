"""Integrate alternate-camera manual outlines into the new village input."""
import json,copy,numpy as np,cv2
from rebuild_v4_arch_geometry import *
P=OUT;path=P/'village_mesh_input.json';d=json.loads(path.read_text());bodies={b['id']:b for b in d['entries']};ann={a['id']:a for a in json.loads((P/'census_box_annotations.json').read_text())['entries']};rows={a['id']:a for a in json.loads((P/'manual_recovery_annotations.json').read_text())};updates=json.loads((P/'manual_recovery_results.json').read_text());audit=[]
for a in updates:
 bid=a['id'];b=bodies.get(bid)
 if b is None:
  src=ann.get(bid,ann.get(a.get('parent_id'),{}));b=copy.deepcopy(src);b.update(id=bid,name=src.get('note','Source recovered attached wing')+' / alternate view',roof_type=src.get('roof_type','flat'),source_ids=[bid],source_role='main_or_wing_pending');bodies[bid]=b
 b.update(footprint_world=a['footprint_world'],roof_edge_height=a['roof_edge_height'],observed_roof_surface_height=a['roof_edge_height']-.30,ridge_height=a['roof_edge_height'],base_height=a['base_height'],primary_source_image=a['source_image'],source_image=a['source_image'],source_polygon_px=a['polygon_px'],fit=a['fit'],geometry_method='manually reviewed alternate-source roof polygon with frozen camera and source-derived height',dense_surface_points=a['dense_points'],manual_recovery_evidence={k:a[k] for k in ['dense_peak','dense_z_quantiles','photometric_evidence']})
 for key in ['floor_count','source_role','parent_id']:
  value=rows[bid].get(key)
  if value is not None:b[key]=value
 b['floor_status']='visually reviewed facade count or source-specific attached component';b['source_partial']=bid in ['V0356','V0501'];b['completion_status']='alternate camera roof extent recovered; full model view review required'
 im=cv2.imread(str(ROOT/'sfm/images'/a['source_image']));mask=np.zeros(im.shape[:2],np.uint8);cv2.fillPoly(mask,[np.round(a['polygon_px']).astype(int)],255);rgb=np.median(im[mask>0][:,::-1],axis=0)/255;b['source_roof_rgb']=(rgb*255).astype(int).tolist();b['roof_color']=b['source_roof_rgb'];audit.append(dict(id=bid,image=a['source_image'],z=a['roof_edge_height'],fit_rms_px=a['fit']['rms_px'],partial=b['source_partial']))
for bid,role,n in [('V0234','wing',2),('V0236','wing',2)]:
 if bid in bodies:bodies[bid].update(source_role=role,floor_count=n)
if 'V0366' in bodies:bodies['V0366'].update(base_height=bodies['V0366']['roof_edge_height']-2.35,roof_type='metal',floor_count=1,source_role='shed',base_evidence='single small shed body visually identified; height inferred from relative source scale')
if 'V0464' in bodies:bodies['V0464'].update(base_height=bodies['V0464']['roof_edge_height']-3.0)
# The old fragment belonged to a low flat red courtyard roof. Its support is too weak
# to retain the erroneous 19-unit narrow slice as a four-storey house.
if 'V0201' in bodies:
 bodies['V0201']['needs_roof_extent_review']=True
d['entries']=list(bodies.values());d['unresolved']=[u for u in d['unresolved'] if u['id'] not in bodies];d['manual_recovery_changes']=audit;path.write_text(json.dumps(d,ensure_ascii=False));(P/'manual_recovery_audit.json').write_text(json.dumps(audit,indent=2));print('APPLIED',len(audit),'BODIES',len(bodies),'UNRESOLVED',d['unresolved'],flush=True)
for sec in [0,44,64,90,120,256,262]:
 name=f'frame_{sec:06.2f}.jpg';im=cv2.imread(str(ROOT/'sfm/images'/name))
 for i,b in enumerate(d['entries']):
  xy=np.array(b['footprint_world']);v=project(np.column_stack([xy,np.full(len(xy),b['roof_edge_height'])]),name)
  if not np.isfinite(v).all() or (v[:,0].max()<0) or (v[:,0].min()>2400) or (v[:,1].max()<0) or (v[:,1].min()>1350):continue
  v=np.round(v).astype(np.int32);c=tuple(int(t) for t in cv2.cvtColor(np.uint8([[[i*43%180,210,250]]]),cv2.COLOR_HSV2BGR)[0,0]);cv2.polylines(im,[v],True,c,2);ctr=v.mean(0).astype(int);cv2.putText(im,b['id'],tuple(ctr),cv2.FONT_HERSHEY_SIMPLEX,.42,(0,0,0),3);cv2.putText(im,b['id'],tuple(ctr),cv2.FONT_HERSHEY_SIMPLEX,.42,c,1)
 cv2.imwrite(str(P/f'village_geometry_{sec:03}.jpg'),im,[cv2.IMWRITE_JPEG_QUALITY,94])
