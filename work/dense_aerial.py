"""Conservative CPU stereo patches from recovered camera poses.

This is a visible-surface draft, not a watertight survey model. Left/right
disparity consistency and local sparse-depth support reject obvious mismatches.
No unseen wall or water surface is synthesized by this stage.
"""
import argparse, json, math
from pathlib import Path
import cv2
import numpy as np
import pycolmap
from scipy.spatial import cKDTree

def pose(image):
    p=image.cam_from_world()
    return p.rotation.matrix(),p.translation

def camera_cv(camera,scale):
    assert camera.model_name=='SIMPLE_RADIAL',camera.model_name
    f,cx,cy,k=camera.params
    return np.array([[f*scale,0,cx*scale],[0,f*scale,cy*scale],[0,0,1]]),np.array([k,0,0,0,0.])

def reconstruct_pair(rec,images,left,right,out,width=1280):
    a,b=images[left],images[right]
    ca,cb=rec.cameras[a.camera_id],rec.cameras[b.camera_id]
    scale=width/ca.width;size=(width,round(ca.height*scale))
    K1,d1=camera_cv(ca,scale);K2,d2=camera_cv(cb,scale)
    A,at=pose(a);B,bt=pose(b)
    relR=B@A.T;relt=bt-relR@at
    R1,R2,P1,P2,Q,roi1,roi2=cv2.stereoRectify(K1,d1,K2,d2,size,relR,relt.reshape(3,1),
        flags=cv2.CALIB_ZERO_DISPARITY,alpha=1)
    vertical=bool(abs(P2[1,3])>abs(P2[0,3]));axis=1 if vertical else 0
    maps1=cv2.initUndistortRectifyMap(K1,d1,R1,P1,size,cv2.CV_32FC1)
    maps2=cv2.initUndistortRectifyMap(K2,d2,R2,P2,size,cv2.CV_32FC1)
    im1=cv2.resize(cv2.imread(str(out.parent/'images'/left)),size)
    im2=cv2.resize(cv2.imread(str(out.parent/'images'/right)),size)
    rect1=cv2.remap(im1,*maps1,cv2.INTER_LINEAR)
    rect2=cv2.remap(im2,*maps2,cv2.INTER_LINEAR)
    obs=[p for p in a.points2D if p.has_point3D() and rec.points3D[p.point3D_id].error<2
         and rec.points3D[p.point3D_id].track.length()>=3]
    if len(obs)<60:return {'left':left,'right':right,'status':'insufficient_sparse_support'}
    sx=np.array([rec.points3D[p.point3D_id].xyz for p in obs])
    uv=np.array([p.xy for p in obs])*scale
    depth=(sx@A.T+at)[:,2]
    rectxyz=(sx@A.T+at)@R1.T
    sparse_disp=-P2[axis,3]/rectxyz[:,2]
    sparse_disp=sparse_disp[np.isfinite(sparse_disp)&(rectxyz[:,2]>0)]
    if len(sparse_disp)<60:return {'left':left,'right':right,'status':'invalid_rectification'}
    lo,hi=np.percentile(sparse_disp,[2,98]);lo=math.floor(lo)-12;hi=math.ceil(hi)+12
    nd=int(math.ceil((hi-lo)/16)*16)
    if nd>384:return {'left':left,'right':right,'status':'excessive_disparity_range','range':nd}
    gray1=cv2.cvtColor(rect1,cv2.COLOR_BGR2GRAY);gray2=cv2.cvtColor(rect2,cv2.COLOR_BGR2GRAY)
    if vertical:gray1=gray1.T.copy();gray2=gray2.T.copy()
    def matcher(md):
        return cv2.StereoSGBM_create(minDisparity=md,numDisparities=nd,blockSize=5,
            P1=8*25,P2=32*25,disp12MaxDiff=1,uniquenessRatio=12,
            speckleWindowSize=120,speckleRange=2,preFilterCap=31,mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY)
    disp=matcher(lo).compute(gray1,gray2).astype(np.float32)/16
    rightmin=-lo-nd
    reverse=matcher(rightmin).compute(gray2,gray1).astype(np.float32)/16
    yy,xx=np.indices(disp.shape);rx=np.rint(xx-disp).astype(int)
    valid=(disp>lo)&(rx>=0)&(rx<disp.shape[1])
    rd=reverse[yy,np.clip(rx,0,disp.shape[1]-1)]
    valid&=(rd>rightmin)&(np.abs(disp+rd)<=1.0)
    if vertical:disp=disp.T.copy();valid=valid.T.copy()
    xyzrect=cv2.reprojectImageTo3D(disp,Q)
    xyzcam=xyzrect@R1
    xyz=(xyzcam-at)@A
    z=xyzcam[:,:,2]
    valid&=np.isfinite(xyz).all(axis=2)&(z>0)
    mx,my=maps1
    valid&=(mx>3)&(mx<size[0]-4)&(my>3)&(my<size[1]-4)
    # A flat patch is weak evidence even when the stereo optimizer finds a match.
    g=cv2.cvtColor(rect1,cv2.COLOR_BGR2GRAY).astype(np.float32)
    variance=cv2.blur(g*g,(7,7))-cv2.blur(g,(7,7))**2
    valid&=variance>20
    valid[:4]=False;valid[-4:]=False;valid[:,:4]=False;valid[:,-4:]=False
    valid[1::2]=False;valid[:,1::2]=False
    y,x=np.nonzero(valid)
    src=np.column_stack((mx[y,x],my[y,x]))
    dist,ix=cKDTree(uv).query(src,k=5)
    supportdepth=np.median(depth[ix],axis=1)
    keep=(dist[:,0]<45)&(np.abs(z[y,x]-supportdepth)<supportdepth*.12)
    y,x=y[keep],x[keep]
    points=xyz[y,x].astype(np.float32);colors=rect1[y,x,::-1]
    source_uv=np.column_stack((mx[y,x],my[y,x]))/scale
    stem=f'{Path(left).stem}__{Path(right).stem}'
    np.savez_compressed(out/(stem+'.npz'),xyz=points,rgb=colors,uv=source_uv,
        rect_xy=np.column_stack((x,y)),rect_size=np.array(size))
    preview=rect1.copy();mask=np.zeros(valid.shape,np.uint8);mask[y,x]=255
    mask=cv2.dilate(mask,np.ones((3,3),np.uint8))
    preview[mask==0]=(preview[mask==0]*.18).astype(np.uint8)
    cv2.imwrite(str(out/(stem+'.jpg')),preview)
    return dict(left=left,right=right,status='computed',points=len(points),
                disparity_range=[lo,lo+nd],vertical=vertical)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path)
    ap.add_argument('--model',type=int,default=0);ap.add_argument('--limit',type=int)
    a=ap.parse_args();rec=pycolmap.Reconstruction(a.root/'sparse'/str(a.model))
    images={i.name:i for i in rec.images.values() if i.has_pose}
    out=a.root/'dense';out.mkdir(exist_ok=True)
    pairs=[(t,t+4) for t in list(range(0,105,4))+list(range(244,265,4))]
    if a.limit:pairs=pairs[:a.limit]
    results=[]
    cv2.setNumThreads(4)
    for t,u in pairs:
        left,right=f'f{t:06.2f}.jpg',f'f{u:06.2f}.jpg'
        if left not in images or right not in images:continue
        r=reconstruct_pair(rec,images,left,right,out)
        results.append(r);print(json.dumps(r),flush=True)
        (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
