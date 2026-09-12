"""Saved-file integrity and architectural detail coverage audit."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
root=Path.cwd();out=root/'outputs/rectangular-photo-refinement';data=json.loads((root/'work/buildings/v2/inventory.json').read_text())['buildings'];result={'checks':{},'buildings':[]};parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'))
cols={c.name.split(' | ')[0]:c for c in parent.children};result['checks']['inventory_exactly_matches_scene']=set(cols)=={b['id'] for b in data};result['checks']['no_external_linked_libraries']=len(bpy.data.libraries)==0
for b in data:
 c=cols[b['id']];names=[]
 for o in c.objects:
  names.append(o.name)
  for item in json.loads(o.get('original_components','[]')):names.append(item['name'] if isinstance(item,dict) else item)
 finite=True;zero=0;vertices=0;wall_bounds=True;footprint=np.array(b['roof_world']);base=b['base_height'];roof=b['roof_height']
 for o in c.objects:
  if o.type=='MESH':
   a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a);finite &= bool(np.isfinite(a).all());vertices+=len(o.data.vertices)
   polygons=list(o.data.polygons)
   for component in json.loads(o.get('original_components','[]')):
    if 'Wall panel with true opening' not in component['name']:continue
    polys=polygons[component['first_polygon']:component['first_polygon']+component['polygon_count']];ix=list({int(i) for poly in polys for i in poly.vertices});xyz=np.array([o.matrix_world@o.data.vertices[i].co for i in ix]);dist=[]
    for v,w in zip(footprint,np.roll(footprint,-1,axis=0)):
     edge=w[:2]-v[:2];t=np.clip(((xyz[:,:2]-v[:2])@edge)/(edge@edge),0,1);dist.append(np.linalg.norm(xyz[:,:2]-(v[:2]+t[:,None]*edge),axis=1))
    wall_bounds &= bool((np.min(dist,axis=0)<.245).all() and (xyz[:,2]>=base-.005).all() and (xyz[:,2]<=roof+.005).all())
   area=np.empty(len(o.data.polygons),np.float32);o.data.polygons.foreach_get('area',area);zero+=int((area<1e-11).sum())
 # Verify the actual saved ground slab, not merely inventory metadata.
 slab_ok=False
 for o in c.objects:
  if o.type!='MESH':continue
  for comp in json.loads(o.get('original_components','[]')):
   if 'Ground floor closed slab' not in comp['name']:continue
   ix=set(i for poly in list(o.data.polygons)[comp['first_polygon']:comp['first_polygon']+comp['polygon_count']] for i in poly.vertices);v=np.array([o.data.vertices[i].co[:] for i in ix]);dims=np.ptp(v,axis=0);slab_ok=bool(len(ix)==8 and abs(dims[0]-b['rectangle']['width'])<1e-4 and abs(dims[1]-b['rectangle']['depth'])<1e-4 and len(np.unique(np.round(v[:,0],4)))==2 and len(np.unique(np.round(v[:,1],4)))==2)
 checks={'saved_ground_slab_is_rectangle':slab_ok,'wall_panels_within_building_envelope':wall_bounds,'finite_mesh_coordinates':finite,'has_floor':any('Ground floor closed slab' in n for n in names),'has_wall_panels':any('Wall panel' in n for n in names),'has_actual_openings':int(c.get('opening_count',0))>0,'has_window_frames_or_unfinished_openings':b['type']=='construction' or any('frame' in n.lower() for n in names),'has_roof_detail':any(any(k in n for k in ['Roof slab expansion','Roof slab transverse','Roof drain','Individual overlapping','Standing roof seam','glazed roof','Glazed tile rib','column reinforcement']) for n in names),'has_drainage':any('downpipe' in n for n in names),'has_materials':all(len(o.data.materials)>0 for o in c.objects if o.type in ('MESH','CURVE')),'no_degenerate_mesh_faces':zero==0}
 result['buildings'].append(dict(id=b['id'],name=b['name'],type=b['type'],objects=len(c.objects),vertices=vertices,openings=int(c.get('opening_count',0)),checks=checks,passed=all(checks.values())))
objects=sorted([o for c in bpy.data.collections if c.name.startswith(('01 TARGET','02 TARGET','03 TARGET')) for o in c.objects],key=lambda o:o.name);h=hashlib.sha256()
for ob in objects:
 h.update(ob.name.encode());h.update(ob.type.encode());h.update(np.array(ob.matrix_world,dtype='<f8').tobytes())
 if ob.type=='MESH':
  v=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',v);h.update(v.tobytes());i=np.empty(len(ob.data.loops),np.int32);ob.data.loops.foreach_get('vertex_index',i);h.update(i.tobytes())
 elif ob.type=='CURVE':
  for sp in ob.data.splines:h.update(np.array([p.co[:] for p in sp.points],dtype='<f4').tobytes())
  h.update(str(ob.data.bevel_depth).encode())
result['landmark']=dict(objects=len(objects),geometry_sha256=h.hexdigest());result['checks']['landmark_retained_geometry_unchanged']=len(objects)==int(bpy.context.scene.get('clean_landmark_object_count',681)) and h.hexdigest()==bpy.context.scene.get('clean_landmark_geometry_sha256','255a0e56df3da9dc34ff01b34bc466c80d72a7cb1320fd116e7ca0504e539bb3');result['checks']['source_images_packed']=all(i.packed_file for i in bpy.data.images if i.source=='FILE');result['checks']['old_surface_and_proxy_collections_hidden']=all(c.hide_render for c in bpy.data.collections if c.name.startswith(('04 ','06 ','09 ','10 ')));result['checks']['no_override_saved']=bpy.context.scene.view_layers[0].material_override is None;alignment=json.loads((root/'work/buildings/v2/final_alignment_audit.json').read_text());result['checks']['no_intersecting_residential_cores']=len(alignment['core_intersections'])==0;result['checks']['all_building_checks_pass']=all(b['passed'] for b in result['buildings']);result['counts']=dict(new_units=len(data),total_units_including_landmark=len(data)+1,new_objects=sum(b['objects'] for b in result['buildings']),mesh_vertices=sum(b['vertices'] for b in result['buildings']),openings=sum(b['openings'] for b in result['buildings']),packed_images=sum(bool(i.packed_file) for i in bpy.data.images));result['checks']['new_architecture_planar_faces_flat_shaded']=all(not p.use_smooth for c in cols.values() for o in c.objects if o.type=='MESH' for p in o.data.polygons);
if bpy.context.scene.get('clean_structure'):
 result['checks']['no_photographic_textures']=not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes) and not any(i.source=='FILE' for i in bpy.data.images)
 result['checks']['no_camera_backgrounds']=not any(c.background_images for c in bpy.data.cameras)
 result['checks']['no_photo_ground']=not any(c.name.startswith('12 ') for c in bpy.data.collections)
result['saved_file']=bpy.data.filepath;result['passed']=all(result['checks'].values());(out/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(dict(checks=result['checks'],counts=result['counts'],failed=[b for b in result['buildings'] if not b['passed']]),ensure_ascii=False,indent=2))
