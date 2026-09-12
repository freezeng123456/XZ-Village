from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1440,724),(242,242,238));d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24)
left=Image.open('work/target/t48.jpg').crop((1460,1400,2300,2160));right=Image.open('outputs/Target_Realistic_Closeup.png')
for x,img,label in [(16,left,'原视频 · 48 秒'),(736,right,'Blender · 重点建筑重建')]:
 d.text((x,12),label,font=font,fill=(30,35,33));img=img.resize((688,622),Image.Resampling.LANCZOS);im.paste(img,(x,52))
d.text((16,688),'可见外观对照；实际尺寸、遮挡立面与周边完整几何尚未校准。',font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19),fill=(70,75,72))
im.save('outputs/Target_Reference_Comparison.jpg',quality=95)
