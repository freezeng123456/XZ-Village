"""Prepare supported surfaces, cameras and evidence for Blender and reviewers."""
import json
from pathlib import Path
import cv2,numpy as np,pycolmap
from scipy.spatial import cKDTree
from aerial_common import load_main

root=Path('work/aerial');sfm=root/'sfm';out=root/'package';out.mkdir(exist_ok=True)
alignment=json.loads((root/'alignment.json').read_text())
R=np.array(alignment['rotation']);shift=np.array(alignment['translation']);scale=alignment['scale']
def transform(p):return np.asarray(p)@R.T*scale+shift
r=load_main(sfm);images={i.name:i for i in r.images.values() if i.has_pose}
parts=[]
for p in sorted((sfm/'flow').glob('*.npz')):
    z=np.load(p);xyz=transform(z['xyz']);keep=(xyz[:,0]>-240)&(xyz[:,0]<140)&(xyz[:,1]>-175)&(xyz[:,1]<300)&(xyz[:,2]>-4)&(xyz[:,2]<55)
    # The editable landmark occupies this footprint; retain its original geometry.
    keep&=~((xyz[:,0]>-.5)&(xyz[:,0]<10.8)&(xyz[:,1]>-2.1)&(xyz[:,1]<9.7)&(xyz[:,2]<13))
    if keep.sum()<500:continue
    parts.append(dict(name=p.stem,xyz=xyz[keep],rgb=z['rgb'][keep],xy=z['rect_xy'][keep],uv=z['uv'][keep],size=z['rect_size']))
xyz=np.concatenate([p['xyz'] for p in parts]);group=np.concatenate([np.full(len(p['xyz']),i,np.int16) for i,p in enumerate(parts)])
tree=cKDTree(xyz);offset=0;report=[];allpoints=[];allcolors=[]
for i,p in enumerate(parts):
    name=p['name'];verts=p['xyz'];camera=transform(images[name.split('__')[0]+'.jpg'].projection_center())
    tolerance=np.clip(.15+np.linalg.norm(verts-camera,axis=1)*.0025,.25,.75)
    distance,index=tree.query(verts,k=24,workers=4)
    support=np.any((group[index]!=i)&(distance<tolerance[:,None]),axis=1)
    grid=np.full((int(p['size'][1]),int(p['size'][0])),-1,np.int32)
    xy=p['xy'];grid[xy[support,1],xy[support,0]]=np.nonzero(support)[0]
    a=grid[:-2,:-2];b=grid[:-2,2:];c=grid[2:,:-2];d=grid[2:,2:]
    faces=np.concatenate((np.stack((a,b,c),axis=-1).reshape(-1,3),np.stack((b,d,c),axis=-1).reshape(-1,3)))
    faces=faces[(faces>=0).all(axis=1)]
    edges=np.linalg.norm(verts[faces]-verts[np.roll(faces,1,axis=1)],axis=2)
    faces=faces[(edges.max(axis=1)<1.8)&(edges.max(axis=1)<np.maximum(edges.min(axis=1),1e-5)*12)]
    if len(faces):
        used,remap=np.unique(faces,return_inverse=True)
        np.savez_compressed(out/(name+'.npz'),xyz=verts[used].astype(np.float32),rgb=p['rgb'][used],
                            faces=remap.reshape(-1,3).astype(np.int32),uv=p['uv'][used])
    allpoints.append(verts[support]);allcolors.append(p['rgb'][support])
    row=dict(name=name,candidates=len(verts),cross_pair_supported=int(support.sum()),triangles=len(faces))
    report.append(row);print(json.dumps(row),flush=True)
cloud=np.concatenate(allpoints);rgb=np.concatenate(allcolors)
voxel=np.floor(cloud/.16).astype(np.int32);_,indices=np.unique(voxel,axis=0,return_index=True)
cloud=cloud[indices].astype(np.float32);rgb=rgb[indices]
np.savez_compressed(out/'cloud.npz',xyz=cloud,rgb=rgb)
ply=np.empty(len(cloud),dtype=[('x','<f4'),('y','<f4'),('z','<f4'),('r','u1'),('g','u1'),('b','u1')])
for j,k in enumerate(['x','y','z']):ply[k]=cloud[:,j]
for j,k in enumerate(['r','g','b']):ply[k]=rgb[:,j]
with (out/'Village_Observed_Points.ply').open('wb') as f:
    f.write(('ply\nformat binary_little_endian 1.0\ncomment Units are nominal metres, not surveyed\n'
             f'element vertex {len(ply)}\nproperty float x\nproperty float y\nproperty float z\n'
             'property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n').encode());ply.tofile(f)
cameras=[]
for name,im in sorted(images.items()):
    camera=r.cameras[im.camera_id];rot=R@im.cam_from_world().rotation.matrix().T@np.diag([1,-1,-1])
    matrix=np.eye(4);matrix[:3,:3]=rot;matrix[:3,3]=transform(im.projection_center())
    cameras.append(dict(name=name,time_seconds=float(name[1:-4]),matrix=matrix.tolist(),
        focal_pixels=float(camera.params[0]),width=camera.width,height=camera.height))
(out/'cameras.json').write_text(json.dumps(cameras,indent=2)+'\n')
# Undistorted reference for matching a standard Blender pinhole camera.
camera=r.cameras[images['f048.00.jpg'].camera_id];f,cx,cy,k=camera.params
K=np.array([[f,0,cx],[0,f,cy],[0,0,1.]])
im=cv2.imread(str(sfm/'images/f048.00.jpg'));cv2.imwrite(str(out/'Reference_48s_Undistorted.jpg'),cv2.undistort(im,K,np.array([k,0,0,0,0.])))
summary=dict(raw_candidates=len(xyz),supported_points_before_voxel=sum(p['cross_pair_supported'] for p in report),
    cloud_points=len(cloud),triangles=sum(p['triangles'] for p in report),parts=report,
    cross_pair_rule='Nearest point from another disjoint two-frame pair within 0.25 to 0.75 nominal metres, depth-adaptive; necessary consistency check, not a survey accuracy bound.',
    limitations='Partial visible surfaces. No watertight reconstruction. Water and occluded/textureless regions are absent. Nominal scale inherited from 7.5 m visual roof-width estimate.')
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='parts'}),flush=True)
