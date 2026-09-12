import bpy, math, os
from mathutils import Vector
out=os.path.abspath('outputs'); s=bpy.context.scene
for ob in bpy.data.objects:
 if ob.name.startswith('Solar panel'): ob.rotation_euler=(0,0,0)
def orig(x,y): return -1+43*math.exp(-((x+110)/150)**2-((y-320)/95)**2)+22*math.exp(-((x-170)/130)**2-((y-360)/95)**2)
def height(x,y):
 t=max(0,min(1,(y-250)/65)); t=t*t*(3-2*t)
 edge=max(0,min(1,(x+360)/45,(392-x)/45,(536-y)/35))
 return -.24+(orig(x,y)+.24)*t*edge
hill=bpy.data.objects['Low wooded hills']
for v in hill.data.vertices: v.co.z=height(v.co.x,v.co.y)
for ob in list(bpy.data.collections['05 Woodland and hills'].objects):
 if ob.name.startswith('Tree crown') and ob.location.y>250:
  x,y=ob.location.x,ob.location.y; ob.location.z+=height(x,y)-orig(x,y)
 elif ob.name.startswith('Tree trunk'):
  p=ob.data.splines[0].points[0]; x,y=p.co.x,p.co.y
  if y>250:
   dz=height(x,y)-orig(x,y)
   for p in ob.data.splines[0].points: p.co.z+=dz
# Frame the central village, keeping the edge of the working landscape outside view.
cam=bpy.data.objects['01 Drone view - pond and village']; cam.location=(205,-300,255); cam.rotation_euler=(Vector((-48,10,0))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=47
s.camera=cam; s.cycles.device='CPU'; s.cycles.samples=24
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Village_Reconstruction.blend'))
for camname,name in [('01 Drone view - pond and village','Village_Overview.png'),('03 Pond bridge detail','Village_Pond_Detail.png')]:
 s.camera=bpy.data.objects[camname]; s.render.filepath=os.path.join(out,name); bpy.ops.render.render(write_still=True)
print('REFINED AND RENDERED',flush=True)
