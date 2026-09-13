"""Render the current pilot geometry with one neutral material from both flights."""
from pathlib import Path
import json
import bpy

root = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root / 'Village_Rebuilt_Master.blend'))
data = json.loads((root / 'data/architecture_geometry.json').read_text())
pilot_ids = {entry['id'] for entry in data['entries'] if entry['id'].startswith('P')}
keep = {obj for col in bpy.data.collections if col.name.split(' | ')[0] in pilot_ids for obj in col.objects}
for obj in list(bpy.context.scene.objects):
    if obj.type in {'MESH', 'CURVE'} and obj not in keep:
        bpy.data.objects.remove(obj, do_unlink=True)
mat = bpy.data.materials.new('Neutral geometry review')
mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.62, .62, .62, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .85
for obj in keep:
    obj.hide_render = False
    obj.data.materials.clear()
    obj.data.materials.append(mat)
out = root / 'pilot'
out.mkdir(exist_ok=True)
scene = bpy.context.scene
scene.render.resolution_percentage = 75
scene.render.film_transparent = True
scene.cycles.samples = 32
for sec in [44, 256]:
    camera = next(camera for camera in data['cameras'] if camera['name'] == f'source_{sec:03}')
    scene.camera = bpy.data.objects[camera['name']]
    scene.render.resolution_x = camera['width']
    scene.render.resolution_y = camera['height']
    scene.render.filepath = str(out / f'Neutral_{sec:03}.png')
    bpy.ops.render.render(write_still=True)
scene.camera = bpy.data.objects['source_044']
scene['review_scope'] = 'Current P-series pilot geometry with uniform neutral material. No claim of complete courtyard coverage.'
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'Pilot_Neutral.blend'))
(out / 'pilot_ids.json').write_text(json.dumps(sorted(pilot_ids), indent=2))
