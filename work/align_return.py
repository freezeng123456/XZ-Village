import sqlite3,json
from pathlib import Path
import numpy as np,pycolmap
from aerial_common import load_main
root=Path('work/aerial');main=load_main(root/'sfm');ret=pycolmap.Reconstruction(root/'sfm/sparse/2')
db=sqlite3.connect(root/'sfm/database.db'); rows=[]
for pid,n,data in db.execute('SELECT pair_id,rows,data FROM two_view_geometries WHERE rows>0'):
    i,j=pid//2147483647,pid%2147483647
    if i in main.images and j in ret.images: a,b=main.images[i],ret.images[j];swap=False
    elif j in main.images and i in ret.images:a,b=main.images[j],ret.images[i];swap=True
    else:continue
    pairs=np.frombuffer(data,np.uint32).reshape(-1,2)
    if swap:pairs=pairs[:,::-1]
    for ia,ib in pairs:
        pa,pb=a.points2D[int(ia)],b.points2D[int(ib)]
        if pa.has_point3D() and pb.has_point3D():
            rows.append((main.points3D[pa.point3D_id].xyz,ret.points3D[pb.point3D_id].xyz,a.name,b.name,pa.xy,pb.xy))
print('cross model matches',len(rows),flush=True)
if len(rows)<3:raise SystemExit()
X=np.array([r[1] for r in rows]);Y=np.array([r[0] for r in rows])
def fit(x,y):
    xc=x-x.mean(0);yc=y-y.mean(0);u,s,v=np.linalg.svd(yc.T@xc);d=np.eye(3);d[2,2]=np.linalg.det(u@v);R=u@d@v;scale=np.trace(np.diag(s)@d)/(xc*xc).sum();t=y.mean(0)-scale*R@x.mean(0);return scale,R,t
rng=np.random.default_rng(42);best=np.zeros(len(X),bool)
for _ in range(20000):
    ix=rng.choice(len(X),3,replace=False)
    if np.linalg.norm(np.cross(X[ix[1]]-X[ix[0]],X[ix[2]]-X[ix[0]]))<.005:continue
    s,R,t=fit(X[ix],Y[ix]);err=np.linalg.norm(s*X@R.T+t-Y,axis=1);inl=err<.025
    if inl.sum()>best.sum():best=inl
print('inliers',best.sum(),flush=True)
if best.sum()<6:raise SystemExit()
for _ in range(3):s,R,t=fit(X[best],Y[best]);err=np.linalg.norm(s*X@R.T+t-Y,axis=1);best=err<.025
a=json.loads((root/'alignment.json').read_text());AR=np.array(a['rotation']);AT=np.array(a['translation']);AS=a['scale']
out=dict(scale=float(s*AS),rotation=(AR@R).tolist(),translation=(AS*AR@t+AT).tolist(),inlier_count=int(best.sum()),total_matches=len(X),rms_nominal_m=float(np.sqrt(np.mean(err[best]**2))*AS),matches=[dict(main=r[2],ret=r[3],main_xy=r[4].tolist(),ret_xy=r[5].tolist(),error_nominal_m=float(e*AS)) for r,e,b in zip(rows,err,best) if b])
Path('work/buildings/return_alignment_candidate.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='matches'},indent=2))
