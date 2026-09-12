import bpy, json, os
s=bpy.context.scene
data={'objects':len(bpy.data.objects),'collections':{c.name:len(c.objects) for c in bpy.data.collections},
 'scene_metadata':{k:str(v) for k,v in s.items()},
 'cameras':[{'name':o.name,'matrix_world':[list(row) for row in o.matrix_world],
             'lens':o.data.lens,'sensor_width':o.data.sensor_width,
             'shift_x':o.data.shift_x,'shift_y':o.data.shift_y} for o in bpy.data.objects if o.type=='CAMERA'],
 'images':[{'name':i.name,'size':list(i.size),'packed':bool(i.packed_file)} for i in bpy.data.images]}
os.makedirs('work/aerial',exist_ok=True)
with open('work/aerial/baseline_inspection.json','w') as f:json.dump(data,f,indent=2)
print(json.dumps(data,indent=2))
