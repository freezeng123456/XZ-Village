import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path('work/rebuild4/architecture');OUT=P/'final_visuals';OUT.mkdir(exist_ok=True);sc=bpy.context.scene;d=json.loads((P/'village_mesh_input.json').read_text());ids={b['id'] for b in d['entries']};cols={c.name.split(' | ')[0]:c for c in bpy.data.collections if c.name.split(' | ')[0] in ids};checks=dict(expected_units=len(ids),collection_units=len(cols),missing_ids=sorted(ids-set(cols)),file_images=[i.name for i in bpy.data.images if i.source=='FILE'],image_texture_nodes=[m.name for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.type=='TEX_IMAGE'],nonfinite_meshes=[],mesh_vertices=0,curves=0,objects=len(sc.objects))
for ob in sc.objects:
 if ob.type=='MESH':
  vs=np.empty(len(ob.data.vertices)*3);ob.data.vertices.foreach_get('co',vs);checks['mesh_vertices']+=len(ob.data.vertices)
  if not np.isfinite(vs).all():checks['nonfinite_meshes'].append(ob.name)
 elif ob.type=='CURVE':checks['curves']+=1
checks['status']='passed' if not any(checks[k] for k in ['missing_ids','file_images','image_texture_nodes','nonfinite_meshes']) and len(cols)==len(ids) else 'failed';(P/'static_geometry_audit.json').write_text(json.dumps(checks,indent=2));print('STATIC_QA',checks,flush=True)
def bbox(choose):
 vs=np.array([tuple(ob.matrix_world@Vector(c)) for k in choose for ob in cols[k].objects for c in ob.bound_box if ob.type in ['MESH','CURVE']]);return vs.min(0),vs.max(0)
bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam;cam.data.type='ORTHO';cam.data.clip_end=10000;cam.data.clip_start=.05;sc.render.resolution_x=2000;sc.render.resolution_y=1250;sc.render.resolution_percentage=100;sc.cycles.samples=40;sc.render.film_transparent=False;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.43,.50,.52,1)
for name,choose,only in [('Village_Overview',list(ids),False),('Pilot_P011',['P011'],True),('Construction_V0329',['V0329'],True),('Roadside_Homes',['V0480','V0481','V0482','V0483','V0484','V0485','V0486'],True),('Public_Building',['V0490'],True),('Traditional_Hall',['V0111','V0111G'],True)]:
 for c in cols.values():c.hide_render=False
 for ob in sc.objects:
  if ob.type in ['MESH','CURVE']:ob.hide_render=only and not any(ob in cols[k].objects.values() for k in choose)
 lo,hi=bbox(choose);center=(lo+hi)/2;size=hi-lo
 if name=='Village_Overview':v=Vector((.20,-.70,.75));scale=max(size[0],size[1]*.95)*1.18
 elif name=='Roadside_Homes':dd=next(c for c in d['cameras'] if c['name']=='source_090');vv=np.array(dd['center'])-center;vv=vv/max(np.linalg.norm(vv[:2]),1);v=Vector((vv[0],vv[1],.65));scale=max(size[0],size[1])*1.2
 else:
  b=next(b for b in d['entries'] if b['id']==choose[0]);edge=np.array(b['footprint_world'][1])-b['footprint_world'][0];yaw=np.arctan2(edge[1],edge[0]);dd=next((c for c in d['cameras'] if c['name']=='source_'+b.get('source_image','frame_044.00.jpg')[6:9]),d['cameras'][0]);vv=np.array(dd['center'])-center;vv=vv/max(np.linalg.norm(vv[:2]),1);v=Vector((vv[0],vv[1],.70));scale=max(np.linalg.norm(size[:2]),size[2]*1.6)*1.20
 cam.location=Vector(center)+v.normalized()*1200;cam.rotation_euler=(Vector(center)-cam.location).to_track_quat('-Z','Y').to_euler();vv=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]]);vv=(vv-center)@np.array(cam.rotation_euler.to_matrix());cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=max(float(np.ptp(vv[:,0])),float(np.ptp(vv[:,1]))*sc.render.resolution_x/sc.render.resolution_y)*1.15;sc.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True);print('FINAL_VISUAL',name,flush=True)
