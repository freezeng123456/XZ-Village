"""Material-consolidated interactive proxy. The .blend remains the full shader master."""
import bpy,json,math,numpy as np,time
from pathlib import Path
from mathutils import Vector
P=Path('work/rebuild4/architecture').resolve();OUT=P/'web';OUT.mkdir(exist_ok=True);original=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();scene=bpy.data.scenes.new('Interactive village proxy');mats=[]
for title,rough,metal in [('Masonry and foliage',.78,0),('Glazing and water',.28,.18),('Metal fittings',.38,.65)]:
 m=bpy.data.materials.new('Web '+title);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;vc=m.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Source finish';m.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);mats.append(m)
bs=json.loads((P/'village_mesh_input.json').read_text())['entries'];byid={b['id']:b for b in bs};groups={}
for ob in original.objects:
 if ob.type not in ['MESH','CURVE']:continue
 bid=next((c.name.split(' | ')[0] for c in ob.users_collection if c.name.split(' | ')[0] in byid or c.name.startswith('SITE')), 'TERRAIN');groups.setdefault(bid,[]).append(ob)
ledger=[]
for bid,obs in groups.items():
 vert=[];faces=[];cols=[];mi=[];smooth=[];offset=0;omitted=0
 for ob in obs:
  if ob.type=='CURVE' and ob.data.bevel_depth<.017:
   omitted+=len(ob.data.splines);continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh(preserve_all_data_layers=False,depsgraph=deps)
  if not me or not len(me.vertices):continue
  me.calc_loop_triangles();v=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',v);v=v.reshape(-1,3);mat=np.array(ob.matrix_world);wv=v@mat[:3,:3].T+mat[:3,3];tri=np.empty(len(me.loop_triangles)*3,dtype=np.int32);me.loop_triangles.foreach_get('vertices',tri);tri=tri.reshape(-1,3);source=ob.data.materials[0] if ob.data.materials else None
  color=np.array(source.diffuse_color[:3] if source else [.25,.27,.25]);name=source.name.lower() if source else '';kind=1 if any(x in name for x in ['glass','water','solar cells']) else (2 if any(x in name for x in ['steel','metal','aluminum']) else 0)
  rgb=np.broadcast_to(color,(len(v),3)).copy()
  if source and any(x in name for x in ['wall','roof','terrain','site','foliage']):
   # Compact vertex modulation approximates broad finish variation only.
   macro=.5+.5*np.sin(v[:,0]*.48+np.sin(v[:,1]*.71)+v[:,2]*.60);rgb*= (.89+.12*macro[:,None])
  vert.append(wv);faces.append(tri+offset);cols.append(np.c_[np.clip(rgb,0,1),np.ones(len(v))]);mi.extend([kind]*len(tri));smooth.extend([name.startswith('foliage')]*len(tri));offset+=len(v);ev.to_mesh_clear()
 if not vert:continue
 vs=np.vstack(vert);fs=np.vstack(faces);cs=np.vstack(cols);me=bpy.data.meshes.new(bid+' proxy geometry');me.from_pydata(vs.tolist(),[],fs.tolist());me.update()
 for m in mats:me.materials.append(m)
 me.polygons.foreach_set('material_index',mi);me.polygons.foreach_set('use_smooth',smooth);attr=me.color_attributes.new(name='Source finish',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',cs.ravel());ob=bpy.data.objects.new(bid,me);scene.collection.objects.link(ob);ob['source_id']=bid
 if bid in byid:
  b=byid[bid];ob['label']=b['name'];ob['source_image']=b.get('source_image','');ob['source_ids']=b.get('source_ids',[bid]);ob['scale_status']='provisional, no surveyed dimensions'
 ledger.append(dict(id=bid,vertices=len(vs),triangles=len(fs),omitted_subpixel_fitting_splines=omitted,bounds=[vs.min(0).tolist(),vs.max(0).tolist()]));print('WEB',ledger[-1],flush=True)
bpy.context.window.scene=scene
bpy.ops.export_scene.gltf(filepath=str(OUT/'Village_Rebuilt_Web.glb'),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_animations=False,export_extras=True,export_yup=True,export_apply=False,export_attributes=False,export_normals=True,export_texcoords=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=14,export_draco_normal_quantization=10,export_draco_color_quantization=8)
(OUT/'web_geometry_ledger.json').write_text(json.dumps(dict(entries=ledger,vertices=sum(x['vertices'] for x in ledger),triangles=sum(x['triangles'] for x in ledger),status='interactive proxy; broad vertex finish colors, finest fitting rods omitted; full procedural master is architecture.blend'),indent=2));print('WEB COMPLETE',flush=True)
