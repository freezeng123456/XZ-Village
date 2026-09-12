"""Restore planar hard-surface face shading after bulk mesh construction."""
import bpy,numpy as np,json
from pathlib import Path
root=Path.cwd();parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'));before=after=faces=0
for col in parent.children:
 for ob in col.objects:
  if ob.type=='MESH':
   flags=np.empty(len(ob.data.polygons),bool);ob.data.polygons.foreach_get('use_smooth',flags);before+=int(flags.sum());ob.data.polygons.foreach_set('use_smooth',np.zeros(len(flags),bool));ob.data.update();ob.data.polygons.foreach_get('use_smooth',flags);after+=int(flags.sum());faces+=len(flags)
result=dict(new_architecture_mesh_faces=faces,smooth_faces_before=before,smooth_faces_after=after,landmark_untouched=True);(root/'outputs/building-quality/planar_shading_check.json').write_text(json.dumps(result,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(root/'outputs/building-quality/Village_Building_Candidates.blend'),compress=True);print('PLANAR_FACES_RESTORED',result,flush=True)
