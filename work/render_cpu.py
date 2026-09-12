import bpy,os
out=os.path.abspath('outputs')
s=bpy.context.scene
s.cycles.device='CPU'; s.cycles.samples=16
s.render.threads_mode='AUTO'
bpy.context.preferences.filepaths.save_version=0
s.camera=bpy.data.objects['01 Drone view - pond and village']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Village_Reconstruction.blend'))
for cam,name in [('01 Drone view - pond and village','Village_Overview.png'),('03 Pond bridge detail','Village_Pond_Detail.png')]:
 s.camera=bpy.data.objects[cam]; s.render.filepath=os.path.join(out,name); bpy.ops.render.render(write_still=True)
print('RENDERS COMPLETE',len(bpy.data.objects),flush=True)
