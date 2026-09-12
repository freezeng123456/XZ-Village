import cv2,os
from PIL import Image
os.makedirs('work/sfm/images',exist_ok=True)
c=cv2.VideoCapture(r'C:\Users\a9959\Downloads\dji_fly_20260216_134446_0050_1771258754211_video.mp4')
times=sorted(set(list(range(0,106,4))+[45,46,47,48,49,50,54,58,62]+list(range(232,273,3))+[254,260,266]))
for i,t in enumerate(times):
 name=f'f{t:03d}.jpg';existing=f'work/target/t{t}.jpg'
 if os.path.exists(existing):f=cv2.imread(existing)
 else:c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
 if f is None:continue
 f=cv2.resize(f,(1600,900),interpolation=cv2.INTER_AREA);cv2.imwrite('work/sfm/images/'+name,f,[cv2.IMWRITE_JPEG_QUALITY,94])
 print(i+1,len(times),name,flush=True)
