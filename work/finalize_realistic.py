import bpy,bmesh,os
out=os.path.abspath('outputs');s=bpy.context.scene
for o in list(bpy.data.objects):
 if o.name in ['Road immediately beside target','Road surface photo texture'] or o.name.startswith(('Deep window reveal','Recessed window glass')):bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects:
 if o.type=='MESH' and len(o.data.polygons)==6 and len(o.data.vertices)==8:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
s.camera=bpy.data.objects['01 Target detail | original video perspective'];s.render.resolution_x=1400;s.render.resolution_y=1267;s.cycles.samples=48
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Village_Realistic_Target.blend'))
s.render.filepath=os.path.join(out,'Target_Realistic_Closeup.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['02 Village context | source camera'];s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.filepath=os.path.join(out,'Village_Reference_View.png');bpy.ops.render.render(write_still=True)
for o in bpy.data.collections['04 Neighbourhood | video-projected context, approximate depth'].objects:o.hide_render=True
s.camera=bpy.data.objects['03 Inspect model from road'];s.render.resolution_x=1400;s.render.resolution_y=1100
s.view_layers[0].material_override=bpy.data.materials.get('Clay inspection')
if not s.view_layers[0].material_override:
 m=bpy.data.materials.new('Clay inspection');m.diffuse_color=(.5,.52,.54,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.5,.52,.54,1);s.view_layers[0].material_override=m
s.render.filepath=os.path.join(out,'Target_Geometry_Check.png');bpy.ops.render.render(write_still=True)
print('FINAL SAVED AND RENDERED',flush=True)
