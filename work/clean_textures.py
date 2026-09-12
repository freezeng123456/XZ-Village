import cv2,numpy as np,json
im=cv2.imread('work/real_assets/main_front.png');mask=np.zeros(im.shape[:2],np.uint8)
cv2.rectangle(mask,(0,850),(115,1040),255,-1);cv2.rectangle(mask,(344,850),(488,1039),255,-1)
out=cv2.inpaint(im,mask,7,cv2.INPAINT_TELEA);cv2.imwrite('work/real_assets/main_front_clean.png',out)
im=cv2.imread('work/real_assets/main_roof.png');grid=[]
for i in range(15):
 for j in range(18):
  x=int((i+.5)*750/15);y=int((17-j+.5)*900/18);b,g,r=im[max(0,y-5):y+6,max(0,x-5):x+6].mean(axis=(0,1));grid.append('orange' if r>g*1.12 and r>b*1.12 else ('white' if (r+g+b)/3>195 else 'grey'))
json.dump(grid,open('work/real_assets/tile_pattern.json','w'))
