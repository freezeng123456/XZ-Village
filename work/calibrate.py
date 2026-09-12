import cv2,numpy as np,json,os
from PIL import Image
im=cv2.imread('work/target/t48.jpg')
os.makedirs('work/real_assets',exist_ok=True)
def rect(name,pts,w,h):
 src=np.array(pts,np.float32)*2; dst=np.array([(0,0),(w,0),(w,h),(0,h)],np.float32)
 H=cv2.getPerspectiveTransform(src,dst);out=cv2.warpPerspective(im,H,(w,h));cv2.imwrite('work/real_assets/'+name+'.png',out)
rect('main_front',[(803,866),(949,879),(941,1036),(797,1026)],750,1040)
rect('main_roof',[(838,778),(961,788),(942,851),(813,840)],750,900)
rect('lower_front',[(946,928),(979,931),(975,1040),(941,1036)],235,670)
rect('terrace',[(952,838),(998,845),(985,901),(946,897)],260,900)
obj=np.array([(0,0,10.4),(7.5,0,10.4),(0,9,10.4),(7.5,9,10.4),(0,0,0),(7.5,0,0)],np.float64)
img=np.array([(802,860),(951,874),(835,769),(969,780),(797,1026),(941,1036)],np.float64)*2
best=None
for focal in range(1900,3701,25):
 K=np.array([[focal,0,1920],[0,focal,1080],[0,0,1]],np.float64)
 ok,r,t=cv2.solvePnP(obj,img,K,None,flags=cv2.SOLVEPNP_ITERATIVE)
 p,_=cv2.projectPoints(obj,r,t,K,None);err=np.linalg.norm(p[:,0]-img,axis=1).mean()
 if best is None or err<best[0]:best=(err,focal,r,t,K,p)
err,f,r,t,K,p=best;R=cv2.Rodrigues(r)[0]; C=-R.T@t
data=dict(error_pixels=float(err),focal=f,R=R.tolist(),t=t.flatten().tolist(),camera=C.flatten().tolist(),K=K.tolist())
json.dump(data,open('work/real_assets/camera.json','w'),indent=2)
print(data)
for a,b in zip(img,p[:,0]):cv2.circle(im,tuple(a.astype(int)),8,(0,0,255),2);cv2.circle(im,tuple(b.astype(int)),5,(0,255,0),2)
cv2.imwrite('work/real_assets/calibration.jpg',im[1450:2120,1500:2050])
