"""Retain geometric components while organizing them into practical building meshes.

Loose mesh pieces and individual curve splines remain editable. Per-component
names and polygon ranges are saved on each grouped mesh. Original landmark is
not touched. This avoids an unusable 140,000-object village hierarchy.
"""
import bpy,bmesh,json,os,numpy as np
from pathlib import Path
root=Path.cwd();folder=os.environ['BATCH_FOLDER'];out=root/'work/buildings'/folder;parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'));removed=[];checks=[]
for col in parent.children:
 bid=col.name.split(' | ')[0];meshgroups={};curvegroups={};old=list(col.objects);before_faces=sum(len(o.data.polygons) for o in old if o.type=='MESH');before_points=sum(sum(len(sp.points) for sp in o.data.splines) for o in old if o.type=='CURVE');newobs=[]
 for ob in old:
  if ob.type=='MESH':
   if any(k in ob.name.lower() for k in ['slab','substrate','hip roof cap']):
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
   assert all(m.type=='BEVEL' for m in ob.modifiers)
   key=(ob.data.materials[0].as_pointer(),tuple((m.width,m.segments,m.profile) for m in ob.modifiers));meshgroups.setdefault(key,[]).append(ob)
  elif ob.type=='CURVE':
   cu=ob.data;key=(cu.materials[0].as_pointer(),cu.bevel_depth,cu.bevel_resolution,cu.resolution_u);curvegroups.setdefault(key,[]).append(ob)
  else:raise RuntimeError('Unexpected architectural component '+ob.type)
 for gi,(key,obs) in enumerate(meshgroups.items()):
  verts=[];starts=[];totals=[];indices=[];uvs=[];components=[];nv=nl=nf=0
  for ci,ob in enumerate(obs):
   me=ob.data;v=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',v);M=np.array(ob.matrix_world);v=v.reshape(-1,3)@M[:3,:3].T+M[:3,3];verts.append(v.astype(np.float32));ix=np.empty(len(me.loops),np.int32);me.loops.foreach_get('vertex_index',ix);indices.append(ix+nv);st=np.empty(len(me.polygons),np.int32);to=np.empty(len(me.polygons),np.int32);me.polygons.foreach_get('loop_start',st);me.polygons.foreach_get('loop_total',to);starts.append(st+nl);totals.append(to);uv=np.zeros(len(me.loops)*2,np.float32)
   if me.uv_layers:me.uv_layers.active.data.foreach_get('uv',uv)
   uvs.append(uv);components.append(dict(name=ob.name,first_polygon=nf,polygon_count=len(me.polygons)));nv+=len(me.vertices);nl+=len(me.loops);nf+=len(me.polygons)
  me=bpy.data.meshes.new(bid+f' / component mesh {gi:02}');me.vertices.add(nv);me.vertices.foreach_set('co',np.concatenate(verts).ravel());me.loops.add(nl);me.loops.foreach_set('vertex_index',np.concatenate(indices));me.polygons.add(nf);me.polygons.foreach_set('loop_start',np.concatenate(starts));me.polygons.foreach_set('loop_total',np.concatenate(totals));me.update();me.materials.append(obs[0].data.materials[0]);uv=me.uv_layers.new(name='Source UV reference');uv.data.foreach_set('uv',np.concatenate(uvs));ob=bpy.data.objects.new(bid+f' / editable mesh components {gi:02}',me);col.objects.link(ob);ob['building_id']=bid;ob['original_components']=json.dumps(components,ensure_ascii=False);ob['editing']='Independent loose mesh pieces; select linked geometry in Edit Mode.'
  me.polygons.foreach_set('use_smooth',np.zeros(nf,dtype=bool))
  for width,segments,profile in key[1]:mod=ob.modifiers.new('Component edge radius','BEVEL');mod.width=width;mod.segments=segments;mod.profile=profile
  newobs.append(ob)
 for gi,(key,obs) in enumerate(curvegroups.items()):
  cu=bpy.data.curves.new(bid+f' / component curves {gi:02}','CURVE');cu.dimensions='3D';cu.bevel_depth=key[1];cu.bevel_resolution=key[2];cu.resolution_u=key[3];cu.materials.append(obs[0].data.materials[0]);names=[]
  for ob in obs:
   assert np.allclose(np.array(ob.matrix_world),np.eye(4))
   for source in ob.data.splines:
    assert source.type=='POLY';sp=cu.splines.new('POLY');sp.points.add(len(source.points)-1);coords=np.empty(len(source.points)*4,np.float32);source.points.foreach_get('co',coords);sp.points.foreach_set('co',coords);sp.use_cyclic_u=source.use_cyclic_u;names.append(ob.name)
  ob=bpy.data.objects.new(bid+f' / editable curve components {gi:02}',cu);col.objects.link(ob);ob['building_id']=bid;ob['original_components']=json.dumps(names,ensure_ascii=False);ob['editing']='Independent editable curve splines.';newobs.append(ob)
 after_faces=sum(len(o.data.polygons) for o in newobs if o.type=='MESH');after_points=sum(sum(len(sp.points) for sp in o.data.splines) for o in newobs if o.type=='CURVE');assert before_faces==after_faces and before_points==after_points
 col['original_component_count']=len(old);col['object_count']=len(newobs);col['component_organization']='Loose mesh components and independent curve splines grouped per material, retaining full geometry.';checks.append(dict(id=bid,original_objects=len(old),organized_objects=len(newobs),mesh_faces=after_faces,curve_points=after_points,geometry_counts_preserved=True));removed+=old
bpy.data.batch_remove(ids=removed);bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
(out/'component_organization.json').write_text(json.dumps(checks,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Organized_Architecture.blend'),compress=True);print('ORGANIZED',folder,len(checks),sum(x['original_objects'] for x in checks),sum(x['organized_objects'] for x in checks),flush=True)
