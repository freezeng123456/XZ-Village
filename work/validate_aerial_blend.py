"""Read-only audit of the saved continuation, including baseline geometry."""
import bpy,json,numpy as np
from pathlib import Path
s=bpy.context.scene;result={'checks':{},'counts':{},'limitations':[]}
for name,expected in [('01 TARGET | surveyed visually from video 45-48 seconds',407),
('02 TARGET | two-storey annex and terrace',170),('03 TARGET | yard, sink, bins and site details',104)]:
    result['checks'][name]=len(bpy.data.collections[name].objects)==expected
result['checks']['legacy_projection_disabled']=bpy.data.collections['04 Neighbourhood | video-projected context, approximate depth'].hide_render
result['checks']['all_file_images_packed']=all(i.packed_file for i in bpy.data.images if i.source=='FILE')
result['checks']['recovered_camera_count']=sum(o.type=='CAMERA' and o.name.startswith('Video ') for o in bpy.data.objects)==57
result['checks']['structural_drafts_separate']=len(bpy.data.collections['10 STRUCTURAL DRAFT | roof-constrained neighbour volumes'].objects)==10
result['checks']['active_camera_valid']=s.camera is not None and s.camera.type=='CAMERA'
finite=True;degenerate=0;faces=0
for o in bpy.data.collections['06 OBSERVED | multi-view supported surface patches'].objects:
    coords=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',coords);finite&=bool(np.isfinite(coords).all());faces+=len(o.data.polygons)
    area=np.empty(len(o.data.polygons),np.float32);o.data.polygons.foreach_get('area',area);degenerate+=int((area<1e-10).sum())
result['checks']['observed_coordinates_finite']=finite
result['checks']['observed_face_count']=faces==s['Observed_surface_triangles']
result['checks']['no_zero_area_observed_faces']=degenerate==0
result['checks']['no_material_override_saved']=s.view_layers[0].material_override is None
result['counts'].update(objects=len(bpy.data.objects),observed_triangles=faces,degenerate_triangles=degenerate,
    packed_images=sum(bool(i.packed_file) for i in bpy.data.images),structural_drafts=10)
result['limitations']=['Model has intentional gaps and incomplete boundaries.','Hidden facades and ground levels remain approximations.',
    '14 return frames remain in a disconnected coordinate system.','Nominal metres are not survey measurements.']
result['passed']=all(result['checks'].values())
out=Path('outputs/aerial-continuation/evidence');out.mkdir(exist_ok=True)
(out/'blender_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if not result['passed']:raise RuntimeError('Saved project validation failed')
