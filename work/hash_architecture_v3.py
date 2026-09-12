import bpy,json,hashlib,os,numpy as np
from pathlib import Path
h=hashlib.sha256();parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'));vertices=0
for c in sorted(parent.children,key=lambda c:c.name):
 h.update(c.name.encode())
 for ob in sorted(c.objects,key=lambda o:o.get('original_components','')):
  h.update(ob.type.encode());h.update(np.array(ob.matrix_world,dtype='<f8').tobytes());h.update(ob.get('original_components','').encode())
  if ob.type=='MESH':
   a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a);h.update(a.tobytes());i=np.empty(len(ob.data.loops),np.int32);ob.data.loops.foreach_get('vertex_index',i);h.update(i.tobytes());vertices+=len(ob.data.vertices)
  elif ob.type=='CURVE':
   for sp in ob.data.splines:h.update(np.array([p.co[:] for p in sp.points],dtype='<f4').tobytes())
   h.update(str(ob.data.bevel_depth).encode())
r=dict(architecture_geometry_sha256=h.hexdigest(),units=len(parent.children),objects=sum(len(c.objects) for c in parent.children),vertices=vertices,saved_scene=bpy.data.filepath)
p=Path(os.environ.get('HASH_OUT','work/buildings/v3/geometry_digest.json'));p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2));print(r)
