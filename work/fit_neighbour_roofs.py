"""Upgrade the baseline's traced neighbour outlines with multi-view roof heights.

The measured evidence is roof-surface support in nominal coordinates. Extruded
walls and flat caps are an editable structural approximation, not recovered
hidden geometry. Pitched roofs still need separate ridge modelling.
"""
import ast,json
from pathlib import Path
import cv2,numpy as np,pycolmap
from aerial_common import load_main
root=Path('work/aerial');a=json.loads((root/'alignment.json').read_text());R=np.array(a['rotation']);t=np.array(a['translation']);scale=a['scale']
r=load_main(root/'sfm');im=next(i for i in r.images.values() if i.name=='f048.00.jpg');cam=r.cameras[im.camera_id]
C=scale*R@im.projection_center()+t
z=np.load(root/'sfm/flow/f048.00__f050.00.npz');xyz=z['xyz']@R.T*scale+t;uv=z['uv']
source=ast.parse(Path('work/build_realistic.py').read_text());items=[]
accepted={'West attached older concrete house','Northwest weathered courtyard roof',
 'Exposed brick neighbour','Rear blue hipped villa','Rear villa east lower wing',
 'Rear white rooftop','Grey house west of blue villa','White pond villa upper roof',
 'Three storey pond villa','Cream villa west pond'}
for node in source.body:
    if not (isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='context_building'):continue
    name,points,oldz=[ast.literal_eval(q) for q in node.value.args]
    # Visual review rejected the other legacy polygons: several trace facades,
    # balconies or occluded surfaces rather than a complete main roof outline.
    if name not in accepted:continue
    poly=np.array(points,np.float32)/1.2
    mask=np.array([cv2.pointPolygonTest(poly,tuple(p),True)>1.4 for p in uv])
    support=xyz[mask]
    if len(support)<12:continue
    # Most-supported horizontal stratum removes parapets/equipment and walls.
    bins=np.round(support[:,2]/.3).astype(int);values,counts=np.unique(bins,return_counts=True)
    zh=values[counts.argmax()]*.3;inliers=np.abs(support[:,2]-zh)<.5
    if inliers.sum()<12:continue
    height=float(np.median(support[inliers,2]));spread=float(np.std(support[inliers,2]))
    if not 2.5<height<22:continue
    norm=cam.cam_from_img(poly.astype(float));rays=np.column_stack((norm,np.ones(len(norm))))@im.cam_from_world().rotation.matrix()@R.T
    verts=C+rays*((height-C[2])/rays[:,2])[:,None]
    items.append(dict(name=name,roof_vertices=verts.tolist(),height_nominal_m=height,
        support_points=int(inliers.sum()),roof_z_std_nominal_m=spread,source_polygon_px=poly.tolist(),
        source_time=48,evidence='Roof outline from baseline manual trace; height from dense multi-view points. Extruded walls, level ground and flat roof cap approximate; no surveyed scale or recovered hidden facades.'))
(root/'package/neighbour_roofs.json').write_text(json.dumps(items,indent=2)+'\n')
print(json.dumps([dict(name=i['name'],height=i['height_nominal_m'],points=i['support_points']) for i in items],indent=2))
