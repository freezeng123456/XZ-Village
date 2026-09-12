import cv2
from PIL import Image,ImageDraw
c=cv2.VideoCapture(r'C:\Users\a9959\Downloads\dji_fly_20260216_134446_0050_1771258754211_video.mp4')
times=[44,46,47,48,49,252,253,254,266,267,285,290]
sheet=Image.new('RGB',(1600,3*247),(20,20,20)); d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
 c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
 if not ok:continue
 im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.save(f'work/target/t{t}.jpg',quality=97);im.thumbnail((400,225));x=i%4*400;y=i//4*247;sheet.paste(im,(x,y));d.text((x+5,y+227),str(t)+'s',fill='white')
sheet.save('work/target/more.jpg')
