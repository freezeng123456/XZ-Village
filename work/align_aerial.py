"""Anchor SfM to the legacy landmark's *estimated* 7.5 m roof width.

Orientation comes from a robust multi-view roof-plane fit and annotated roof
edge. This retains arbitrary/nominal scale; it is not a physical measurement.
"""
import json
from pathlib import Path
import cv2,numpy as np,pycolmap
from aerial_common import load_main

def fit_plane(x,tol=.0025,trials=800):
    rng=np.random.default_rng(216);best=np.zeros(len(x),bool)
    for _ in range(trials):
        a,b,c=x[rng.choice(len(x),3,replace=False)];n=np.cross(b-a,c-a)
        if np.linalg.norm(n)<1e-10:continue
        n/=np.linalg.norm(n);mask=np.abs((x-a)@n)<tol
        if mask.sum()>best.sum():best=mask
    center=x[best].mean(axis=0);_,_,vt=np.linalg.svd(x[best]-center);n=vt[-1]
    return center,n,best

root=Path('work/aerial/sfm');r=load_main(root)
im=next(i for i in r.images.values() if i.name=='f048.00.jpg');cam=r.cameras[im.camera_id]
data=np.load(root/'flow/f048.00__f050.00.npz');uv=data['uv'];points=data['xyz']
poly=np.array([[699,658],[795,665],[786,705],[682,696]],np.float32)
mask=np.array([cv2.pointPolygonTest(poly,tuple(p),False)>=0 for p in uv])
x=points[mask];center,n,inliers=fit_plane(x)
corners=np.array([[802,860],[951,874],[835,769],[969,780]],float)/1.2
normalized=cam.cam_from_img(corners);R=im.cam_from_world().rotation.matrix();C=im.projection_center()
dirs=np.column_stack((normalized,np.ones(4)))@R
corner3=C+dirs*(((center-C)@n)/(dirs@n))[:,None]
# Front roof corners in the old model's +X direction. Plane normal toward drone.
if n@(C-center)<0:n=-n
xaxis=corner3[1]-corner3[0];xaxis-=n*(xaxis@n);xaxis/=np.linalg.norm(xaxis)
yaxis=np.cross(n,xaxis)
if yaxis@(corner3[2]-corner3[0])<0:raise RuntimeError('Roof orientation is inconsistent')
rotation=np.array([xaxis,yaxis,n])
scale=7.5/np.linalg.norm(corner3[1]-corner3[0])
offset=np.array([0,0,10.65])-scale*rotation@corner3[0]
aligned=scale*corner3@rotation.T+offset
out=dict(reference_image=im.name,roof_polygon_px=poly.tolist(),corners_px=corners.tolist(),
    source_points=len(x),plane_inliers=int(inliers.sum()),plane_fit_rms_nominal_m=float(np.sqrt(np.mean(((x[inliers]-center)@n)**2))*scale),
    nominal_width_m=7.5,scale=float(scale),rotation=rotation.tolist(),translation=offset.tolist(),
    aligned_roof_corners=aligned.tolist(),units='nominal metres, not surveyed',
    uncertainty='Roof width inherits old visual estimate; roof corners and plane are approximate. Do not infer real-world measurement accuracy.')
(root.parent/'alignment.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
# Raw correspondences for review, before any Blender integration.
np.savez_compressed(root.parent/'roof_plane_check.npz',points=x,inliers=inliers,corners=corner3)
