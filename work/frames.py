import cv2, os
from PIL import Image, ImageDraw
p=r'C:\Users\a9959\Downloads\dji_fly_20260216_134446_0050_1771258754211_video.mp4'
c=cv2.VideoCapture(p)
fps=c.get(cv2.CAP_PROP_FPS); n=c.get(cv2.CAP_PROP_FRAME_COUNT); duration=n/fps
print(dict(fps=fps,frames=n,duration=duration,width=c.get(3),height=c.get(4)),flush=True)
os.makedirs('work/frames',exist_ok=True)
sheet=Image.new('RGB',(1440,4*294),(20,20,20)); d=ImageDraw.Draw(sheet)
for i in range(12):
 t=duration*(0.02+i*.087)
 c.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,f=c.read()
 if not ok: continue
 im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)); im.thumbnail((1920,1080)); im.save(f'work/frames/{i:02}.jpg')
 im.thumbnail((480,270)); x=i%3*480; y=i//3*294; sheet.paste(im,(x,y)); d.text((x+5,y+271),f'{i:02} | {t:.1f}s',fill='white')
sheet.save('work/contact.jpg')
