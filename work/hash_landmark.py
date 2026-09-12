import bpy,hashlib,json,sys
from pathlib import Path
import numpy as np
hasher=hashlib.sha256();count=0
objects=sorted([o for c in bpy.data.collections if c.name.startswith(('01 TARGET','02 TARGET','03 TARGET')) for o in c.objects],key=lambda o:o.name)
for ob in objects:
    hasher.update(ob.name.encode());hasher.update(ob.type.encode());hasher.update(np.array(ob.matrix_world,dtype='<f8').tobytes())
    if ob.type=='MESH':
        values=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',values);hasher.update(values.tobytes())
        indices=np.empty(len(ob.data.loops),np.int32);ob.data.loops.foreach_get('vertex_index',indices);hasher.update(indices.tobytes())
    elif ob.type=='CURVE':
        for sp in ob.data.splines:hasher.update(np.array([p.co[:] for p in sp.points],dtype='<f4').tobytes())
        hasher.update(str(ob.data.bevel_depth).encode())
    count+=1
result=dict(objects=count,geometry_sha256=hasher.hexdigest())
dest=Path(sys.argv[sys.argv.index('--')+1]);dest.write_text(json.dumps(result,indent=2)+'\n');print(result)
