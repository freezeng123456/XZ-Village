"""Test wide-view correspondences; all matches remain unaccepted until geometry/visual review."""
import sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path('work/rebuild4/tools/onnx_runtime').resolve()))
import onnxruntime as ort
import numpy as np,cv2

root=Path('work/rebuild4');out=root/'learned_probe';out.mkdir(exist_ok=True)
opts=ort.SessionOptions();opts.intra_op_num_threads=3;opts.inter_op_num_threads=1
net=ort.InferenceSession(str(root/'tools/superpoint_2048_lightglue_end2end.onnx'),sess_options=opts,providers=['CPUExecutionProvider'])
a=cv2.imread(str(root/'sfm/images/frame_044.00.jpg'));b=cv2.imread(str(root/'sfm/images/frame_256.00.jpg'))

def inp(im):
    scale=min(1.,1024/max(im.shape[:2]));w=int(im.shape[1]*scale)//8*8;h=int(im.shape[0]*scale)//8*8
    x=cv2.cvtColor(cv2.resize(im,(w,h)),cv2.COLOR_BGR2GRAY)[None,None].astype(np.float32)/255
    return x,np.array([w/im.shape[1],h/im.shape[0]],np.float32)

for mode,boxa,boxb in [('full',(0,0,2400,1350),(0,0,2400,1350)),('pilot',(250,330,1300,920),(1460,0,2340,570))]:
    aa=a[boxa[1]:boxa[3],boxa[0]:boxa[2]];bb=b[boxb[1]:boxb[3],boxb[0]:boxb[2]]
    for rot in range(4):
        start=time.time();br=np.rot90(bb,rot).copy();x,s0=inp(aa);y,s1=inp(br)
        k0,k1,m0,m1,sc0,sc1=net.run(None,{'image0':x,'image1':y})
        valid=m0[0]>=0;ix=np.where(valid)[0];j=m0[0][valid]
        p=(k0[0][ix]+.5)/s0-.5;qr=(k1[0][j]+.5)/s1-.5
        w,h=bb.shape[1],bb.shape[0]
        if rot==0:q=qr
        elif rot==1:q=np.c_[w-1-qr[:,1],qr[:,0]]
        elif rot==2:q=np.c_[w-1-qr[:,0],h-1-qr[:,1]]
        else:q=np.c_[qr[:,1],h-1-qr[:,0]]
        p+=boxa[:2];q+=boxb[:2]
        F,mask=(cv2.findFundamentalMat(p,q,cv2.USAC_MAGSAC,2.,.999,50000) if len(p)>=8 else (None,None))
        name=f'{mode}_rot{rot}';score=sc0[0][valid]
        np.savez(out/f'{name}.npz',p=p,q=q,score=score,F=F,inlier=mask)
        row=dict(name=name,matches=len(p),inliers=int(mask.sum()) if mask is not None else 0,elapsed=time.time()-start)
        (out/f'{name}.json').write_text(json.dumps(row));print(row,flush=True)
        can=np.hstack([a,b]);rng=np.random.default_rng(914)
        for u,v,s in zip(p,q,score):
            if s<.25:continue
            c=tuple(int(z) for z in rng.integers(50,255,3));cv2.circle(can,tuple(u.astype(int)),5,c,-1);cv2.circle(can,tuple((v+[2400,0]).astype(int)),5,c,-1);cv2.line(can,tuple(u.astype(int)),tuple((v+[2400,0]).astype(int)),c,2)
        cv2.imwrite(str(out/f'{name}.jpg'),cv2.resize(can,(2400,675)))
