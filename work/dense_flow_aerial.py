"""Dense two-view triangulation for forward flight, with explicit quality gates.

DIS flow proposes pixel correspondences; recovered cameras, forward/backward
flow, photometric agreement, ray angle and reprojection reject bad proposals.
It supplies partial observed surfaces, never invented occluded geometry.
"""
import argparse,json
from pathlib import Path
import cv2,numpy as np,pycolmap
from scipy.spatial import cKDTree
from aerial_common import load_main

def process(rec,images,left,right,out):
    a,b=images[left],images[right];ca,cb=rec.cameras[a.camera_id],rec.cameras[b.camera_id]
    width=1280;scale=width/ca.width;size=(width,round(ca.height*scale))
    im1=cv2.resize(cv2.imread(str(out.parent/'images'/left)),size)
    im2=cv2.resize(cv2.imread(str(out.parent/'images'/right)),size)
    g1=cv2.cvtColor(im1,cv2.COLOR_BGR2GRAY);g2=cv2.cvtColor(im2,cv2.COLOR_BGR2GRAY)
    dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    dis.setFinestScale(0)
    flow=dis.calc(g1,g2,None);back=dis.calc(g2,g1,None)
    y,x=np.mgrid[4:size[1]-4:2,4:size[0]-4:2]
    xy=np.column_stack((x.ravel(),y.ravel())).astype(np.float32)
    target=xy+flow[y,x].reshape(-1,2)
    bx,by=target[:,0].reshape(-1,1),target[:,1].reshape(-1,1)
    # OpenCV remap limits individual dimensions to SHRT_MAX.
    def sample(image):
        return np.concatenate([cv2.remap(image,bx[i:i+20000],by[i:i+20000],
            cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT).reshape(-1,*image.shape[2:])
            for i in range(0,len(xy),20000)])
    fb=np.linalg.norm(flow[y,x].reshape(-1,2)+sample(back),axis=1)
    photo=np.abs(g1[y,x].ravel().astype(float)-sample(g2))
    g=g1.astype(np.float32);var=cv2.blur(g*g,(7,7))-cv2.blur(g,(7,7))**2
    keep=(target[:,0]>3)&(target[:,0]<size[0]-4)&(target[:,1]>3)&(target[:,1]<size[1]-4)
    keep&=(fb<.8)&(photo<22)&(var[y,x].ravel()>25)
    xy=xy[keep];target=target[keep]
    uv=xy/scale;uv2=target/scale
    uvn=ca.cam_from_img(uv.astype(np.float64));uvn2=cb.cam_from_img(uv2.astype(np.float64))
    pa,pb=a.cam_from_world(),b.cam_from_world();A=pa.rotation.matrix();B=pb.rotation.matrix()
    h=cv2.triangulatePoints(pa.matrix(),pb.matrix(),uvn.T.copy(),uvn2.T.copy())
    points=(h[:3]/h[3]).T
    ac=points@A.T+pa.translation;bc=points@B.T+pb.translation
    rp=ca.img_from_cam(ac);rp2=cb.img_from_cam(bc)
    error=np.maximum(np.linalg.norm(rp-uv,axis=1),np.linalg.norm(rp2-uv2,axis=1))
    rays=points-a.projection_center();rays2=points-b.projection_center()
    cosine=np.sum(rays*rays2,axis=1)/(np.linalg.norm(rays,axis=1)*np.linalg.norm(rays2,axis=1))
    angle=np.degrees(np.arccos(np.clip(cosine,-1,1)))
    keep=np.isfinite(points).all(axis=1)&(ac[:,2]>0)&(bc[:,2]>0)&(error<.8)&(angle>1.5)&(angle<45)
    obs=[p for p in a.points2D if p.has_point3D() and rec.points3D[p.point3D_id].error<2
         and rec.points3D[p.point3D_id].track.length()>=3]
    suv=np.array([p.xy for p in obs]);sx=np.array([rec.points3D[p.point3D_id].xyz for p in obs])
    sz=(sx@A.T+pa.translation)[:,2]
    dist,ix=cKDTree(suv).query(uv,k=5)
    depth=np.median(sz[ix],axis=1)
    keep&=(dist[:,0]<55)&(np.abs(ac[:,2]-depth)<depth*.10)
    points=points[keep];uv=uv[keep];xy=xy[keep].astype(int)
    colors=im1[xy[:,1],xy[:,0],::-1]
    stem=f'{Path(left).stem}__{Path(right).stem}'
    np.savez_compressed(out/(stem+'.npz'),xyz=points.astype(np.float32),rgb=colors,uv=uv,
        rect_xy=xy,rect_size=np.array(size),error=error[keep],angle=angle[keep])
    mask=np.zeros(g1.shape,np.uint8);mask[xy[:,1],xy[:,0]]=255
    mask=cv2.dilate(mask,np.ones((3,3),np.uint8));preview=im1.copy()
    preview[mask==0]=(preview[mask==0]*.2).astype(np.uint8)
    cv2.imwrite(str(out/(stem+'.jpg')),preview)
    # Compare proposals with sparse correspondences, independent of stereo output.
    bobs={p.point3D_id:p.xy*scale for p in b.points2D if p.has_point3D()}
    residual=[]
    for o in obs:
        if o.point3D_id not in bobs:continue
        q=o.xy*scale;ix,iy=np.rint(q).astype(int)
        if 0<=ix<size[0] and 0<=iy<size[1]:residual.append(np.linalg.norm(q+flow[iy,ix]-bobs[o.point3D_id]))
    return dict(left=left,right=right,points=len(points),median_reprojection_px=float(np.median(error[keep])) if len(points) else None,
        median_ray_angle_deg=float(np.median(angle[keep])) if len(points) else None,
        sparse_flow_check_count=len(residual),sparse_flow_error_median_px=float(np.median(residual)) if residual else None)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--model',type=int)
    ap.add_argument('--start',type=int,default=0);ap.add_argument('--end',type=int,default=76)
    ap.add_argument('--step',type=int,default=4);ap.add_argument('--baseline',type=int,default=2)
    a=ap.parse_args();rec=load_main(a.root) if a.model is None else pycolmap.Reconstruction(a.root/'sparse'/str(a.model))
    images={i.name:i for i in rec.images.values() if i.has_pose}
    out=a.root/'flow';out.mkdir(exist_ok=True);cv2.setNumThreads(4);results=[]
    for t in range(a.start,a.end+1,a.step):
        left,right=f'f{t:06.2f}.jpg',f'f{t+a.baseline:06.2f}.jpg'
        if left not in images or right not in images:continue
        r=process(rec,images,left,right,out);results.append(r);print(json.dumps(r),flush=True)
        (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
