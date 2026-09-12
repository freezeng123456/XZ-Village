"""Source-colour architectural finishes, removing view-dependent facade ghosts."""
import bpy,json,re,os
from pathlib import Path
root=Path.cwd();data=json.loads((root/'work/buildings/surface_finishes.json').read_text());changed=0
for m in bpy.data.materials:
 bid=m.name.split(' / ')[0]
 if bid not in data or not m.use_nodes:continue
 d=data[bid];name=m.name
 if not any(s in name for s in ['wall tone','aged plaster','exposed clay brick','red public hall plaster','visible source','visible roof paving']):continue
 roof='roof paving' in name;rgb=d['roof'] if roof and d['roof'] else d['wall'];match=re.search(r'edge (\d+)',name)
 if match and d['faces'].get(match[1],{}).get('rgb') and d['faces'][match[1]]['pixels']>100 and not d.get('public_hall'):rgb=d['faces'][match[1]]['rgb']
 m.diffuse_color=(*rgb,1);nt=m.node_tree;bsdf=nt.nodes.get('Principled BSDF')
 for link in list(bsdf.inputs['Base Color'].links):nt.links.remove(link)
 ramp=next((n for n in nt.nodes if n.bl_idname=='ShaderNodeValToRGB'),None)
 if ramp:
  ramp.color_ramp.elements[0].color=(*(v*.86 for v in rgb),1);ramp.color_ramp.elements[1].color=(*(min(.9,v*1.08) for v in rgb),1);nt.links.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
 else:bsdf.inputs['Base Color'].default_value=(*rgb,1)
 bsdf.inputs['Roughness'].default_value=.82
 if not roof and d['type']!='gable' and d.get('finish_style')!='weathered_concrete':
  brick=nt.nodes.new('ShaderNodeTexBrick');brick.label='Estimated coherent cladding';exposed=d.get('finish_style')=='exposed_brick';brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=.24 if exposed else .11;brick.inputs['Row Height'].default_value=.075 if exposed else .28;brick.inputs['Mortar Size'].default_value=.006 if exposed else .0012;brick.offset=.5 if exposed else 0;brick.inputs['Color1'].default_value=(*(v*.96 for v in rgb),1);brick.inputs['Color2'].default_value=(*(min(.92,v*1.035) for v in rgb),1);brick.inputs['Mortar'].default_value=(*(v*.71 for v in rgb),1)
  tex=nt.nodes.new('ShaderNodeTexCoord');sep=nt.nodes.new('ShaderNodeSeparateXYZ');combine=nt.nodes.new('ShaderNodeCombineXYZ');nt.links.new(tex.outputs['Object'],sep.inputs[0]);geom=nt.nodes.new('ShaderNodeNewGeometry');normal=nt.nodes.new('ShaderNodeVectorTransform');normal.vector_type='NORMAL';normal.convert_from='WORLD';normal.convert_to='OBJECT';nt.links.new(geom.outputs['Normal'],normal.inputs[0]);cross=nt.nodes.new('ShaderNodeVectorMath');cross.operation='CROSS_PRODUCT';cross.inputs[1].default_value=(0,0,1);nt.links.new(normal.outputs[0],cross.inputs[0]);unit=nt.nodes.new('ShaderNodeVectorMath');unit.operation='NORMALIZE';nt.links.new(cross.outputs[0],unit.inputs[0]);dot=nt.nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';nt.links.new(tex.outputs['Object'],dot.inputs[0]);nt.links.new(unit.outputs[0],dot.inputs[1]);nt.links.new(dot.outputs['Value'],combine.inputs['X']);nt.links.new(sep.outputs['Z'],combine.inputs['Y']);nt.links.new(combine.outputs[0],brick.inputs['Vector']);nt.links.new(brick.outputs['Color'],bsdf.inputs['Base Color']);bump=next((n for n in nt.nodes if n.bl_idname=='ShaderNodeBump'),None)
  if bump:bump.inputs['Distance'].default_value=.012 if exposed else .004;bump.inputs['Strength'].default_value=.3;nt.links.new(brick.outputs['Fac'],bump.inputs['Height'])
 m['finish_evidence']='Dominant source surface colour with inferred continuous construction finish. Image-fragment projection intentionally removed from the render.';changed+=1
s=bpy.context.scene;s['Facade_finish']='Source-sampled colours and continuous inferred construction materials; source photo nodes retained only as unused references.'
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:im.pack()
bpy.context.preferences.filepaths.save_version=0;dest=root/os.environ.get('CLEAN_OUT','outputs/building-quality/Village_Building_Candidates.blend');bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True);print('CONTINUOUS_FINISHES_SAVED',changed,flush=True)
