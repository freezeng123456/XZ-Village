"""Trim standing roof seams to their own traced building footprints."""
import bpy,json,numpy as np
from pathlib import Path
root=Path.cwd();bs=json.loads((root/'work/buildings/visibility/architecture_visibility.json').read_text())['buildings'];parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'));cols={c.name.split(' | ')[0]:c for c in parent.children};report=[]
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def inside(q,poly):
 flag=False
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  edge=b-a
  if abs(cross(q-a,edge))<1e-4*(np.linalg.norm(edge)+1) and (q-a)@(q-b)<1e-4:return True
  if (a[1]>q[1])!=(b[1]>q[1]) and q[0]<(b[0]-a[0])*(q[1]-a[1])/(b[1]-a[1])+a[0]:flag=not flag
 return flag
def clip(a,b,poly):
 d=b[:2]-a[:2];values=[0.,1.]
 for p,q in zip(poly,np.roll(poly,-1,axis=0)):
  e=q-p;den=cross(d,e)
  if abs(den)<1e-10:continue
  t=cross(p-a[:2],e)/den;u=cross(p-a[:2],d)/den
  if 0<t<1 and 0<=u<=1:values.append(t)
 values=sorted(set(values));return [(a+(b-a)*lo,a+(b-a)*hi) for lo,hi in zip(values[:-1],values[1:]) if inside((a+(b-a)*(lo+hi)/2)[:2],poly)]
for b in bs:
 if b['type']!='metal':continue
 poly=np.array(b['roof_world'])[:,:2];col=cols[b['id']];before=after=trimmed=0
 for ob in list(col.objects):
  if ob.type!='CURVE':continue
  names=json.loads(ob.get('original_components','[]'))
  if not any('Raised standing sheet seam' in n for n in names):continue
  old=ob.data;cu=bpy.data.curves.new(old.name+' clipped','CURVE');cu.dimensions='3D';cu.bevel_depth=old.bevel_depth;cu.bevel_resolution=old.bevel_resolution;cu.resolution_u=old.resolution_u;cu.materials.append(old.materials[0]);newnames=[]
  for source,name in zip(old.splines,names):
   points=np.array([p.co[:] for p in source.points]);assert len(points)==2;before+=1
   segments=clip(points[0,:3],points[1,:3],poly) if 'Raised standing sheet seam' in name else [(points[0,:3],points[1,:3])]
   if len(segments)!=1 or any(not np.allclose(p,q) for p,q in zip(segments[0],points[:,:3])):trimmed+=1
   for a,z in segments:
    assert inside(a[:2],poly) and inside(z[:2],poly);sp=cu.splines.new('POLY');sp.points.add(1);sp.points[0].co=(*a,1);sp.points[1].co=(*z,1);newnames.append(name);after+=1
  ob.data=cu;ob['original_components']=json.dumps(newnames,ensure_ascii=False)
 report.append(dict(id=b['id'],seams_before=before,seams_after=after,trimmed_or_removed=trimmed,endpoints_within_roof=True))
(root/'outputs/building-quality/roof_seam_check.json').write_text(json.dumps(report,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(root/'outputs/building-quality/Village_Building_Candidates.blend'),compress=True);print('ROOF_SEAMS_CLIPPED',report,flush=True)
