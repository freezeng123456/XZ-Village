"""Render source-camera crops and clean opposing views of each saved V3 building."""
import bpy,json,os,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
root=Path.cwd();out=root/os.environ.get('REVIEW_OUT','outputs/orthogonal-multiview/review');out.mkdir(parents=True,exist_ok=True);bs=json.loads((root/'work/buildings/v3/inventory.json').read_text())['buildings'];poses=json.loads((root/'work/buildings/visibility/poses.json').read_text());s=bpy.context.scene;parent=next(c for c in bpy.data.collections if c.name.startswith('11 ARCHITECTURE'));cols={c.name.split(' | ')[0]:c for c in parent.children};bs=[b for b in bs if b['id'] in cols];IDs=set(filter(None,os.environ.get('REVIEW_IDS','').split(',')))
if IDs:bs=[b for b in bs if b['id'] in IDs]
if os.environ.get('RETURN_ONLY'):bs=[dict(b,t=256) for b in bs if b['t']!=256]
for c in s.collection.children:
 if c!=parent and not c.name.startswith(('05 ','08 ')):c.hide_render=True
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=int(os.environ.get('REVIEW_SAMPLES','32'));s.cycles.use_denoising=True;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.25;s.view_layers[0].material_override=None
camdata=bpy.data.cameras.new('V3 review camera');cam=bpy.data.objects.new(camdata.name,camdata);s.collection.objects.link(cam);s.camera=cam;camdata.clip_end=5000;manifest=[]
def project(q,p):
 pc=q@np.array(p['rotation']).T+p['translation'];xy=pc[:,:2]/pc[:,2,None];return xy*(1+p['radial']*(xy*xy).sum(1))[:,None]*p['focal']+[800,450]
for b in bs:
 col=cols[b['id']]
 for c in cols.values():c.hide_render=c!=col
 points=np.array([tuple(o.matrix_world@Vector(v)) for o in col.objects for v in o.bound_box]);mn=points.min(0);mx=points.max(0);center=Vector((mn+mx)/2);rad=float(np.linalg.norm(mx-mn));p=poses[str(b['t'])];px=project(points,p);lo=px.min(0)-np.ptp(px,axis=0)*.11;hi=px.max(0)+np.ptp(px,axis=0)*.11;size=hi-lo;mid=(lo+hi)/2;cw,ch=size
 # Expand the crop itself before limiting render aspect, preserving source framing.
 if ch>2*cw:cw=ch/2;lo[0]=mid[0]-cw/2;hi[0]=mid[0]+cw/2
 if ch<cw*.267:ch=cw*.267;lo[1]=mid[1]-ch/2;hi[1]=mid[1]+ch/2
 # Blender pinhole framing uses undistorted bounds; source crop retains measured radial projection.
 pc=points@np.array(p['rotation']).T+p['translation'];upx=pc[:,:2]/pc[:,2,None]*p['focal']+[800,450];ulo=upx.min(0)-np.ptp(upx,axis=0)*.11;uhi=upx.max(0)+np.ptp(upx,axis=0)*.11;mid=(ulo+uhi)/2;cw,ch=uhi-ulo
 if ch>2*cw:cw=ch/2
 if ch<cw*.267:ch=cw*.267
 # Perspective camera retains the reference pose and intrinsic focal length.
 camdata.type='PERSP';camdata.sensor_fit='HORIZONTAL';camdata.sensor_width=36;camdata.lens=p['focal']*36/cw;camdata.shift_x=(mid[0]-800)/cw;camdata.shift_y=(450-mid[1])/cw;M=np.eye(4);M[:3,:3]=np.array(p['rotation']).T@np.diag([1,-1,-1]);M[:3,3]=p['position'];cam.matrix_world=Matrix(M);rw=int(os.environ.get('REVIEW_WIDTH','900'));s.render.resolution_x=rw;s.render.resolution_y=max(160,min(round(rw*2),round(rw*ch/cw)));s.render.filepath=str(out/(b['id']+('_return_view.png' if os.environ.get('RETURN_ONLY') else '_source_view.png')));bpy.ops.render.render(write_still=True)
 manifest.append(dict(id=b['id'],source_time=b['t'],source_crop_1600=[float(x) for x in np.r_[lo,hi]],source_image=p['source'],source_render=str(Path(s.render.filepath).relative_to(root))))
 if os.environ.get('SOURCE_ONLY'):continue
 # Opposing views expose hidden shape and details; no backdrop hides the footprint.
 for side in [0,1]:
  theta=b['rectangle']['angle_radians'];u=Vector((np.cos(theta),np.sin(theta),0));v=Vector((-np.sin(theta),np.cos(theta),0));direction=(u*.7-v+Vector((0,0,.72)))*(1 if side==0 else -1);direction.z=abs(direction.z);cam.location=center+direction*rad*2;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.shift_x=camdata.shift_y=0;s.render.resolution_x=1000;s.render.resolution_y=800;bpy.context.view_layer.update();q=np.array([tuple(cam.matrix_world.inverted()@Vector(x)) for x in points]);camdata.ortho_scale=max(np.ptp(q[:,0])*1.15,np.ptp(q[:,1])*1.25*1.15);s.render.filepath=str(out/(b['id']+f'_oblique_{side}.png'));bpy.ops.render.render(write_still=True)
 print('V3_REVIEW_RENDERED',b['id'],flush=True)
(out/('return_view_manifest.json' if os.environ.get('RETURN_ONLY') else 'source_view_manifest.json')).write_text(json.dumps(manifest,indent=2))

if os.environ.get('AUTO_RETURN') and not os.environ.get('RETURN_ONLY'):
 os.environ['RETURN_ONLY']='1';os.environ['SOURCE_ONLY']='1';exec(compile(Path(__file__).read_text(),__file__,'exec'))
