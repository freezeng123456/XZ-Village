import json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
root=Path.cwd();out=root/'outputs/orthogonal-multiview';tmp=root/'work/buildings/v3';font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',28);small=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',21)
ids=sorted(set(c['id'] for c in json.loads((out/'multiview_changes.json').read_text())))
for page in range((len(ids)+2)//3):
 canvas=Image.new('RGB',(2100,1620),'#eeeee7');d=ImageDraw.Draw(canvas)
 for row,id in enumerate(ids[page*3:page*3+3]):
  d.text((12,row*540+6),id+' · 返程原图 / 返程模型 / 另一侧模型',font=font,fill='#283b3a')
  model=out/f'review/{id}_return_view.png'
  if not model.exists():model=out/f'review/{id}_source_view.png'
  for col,path in enumerate([out/f'reference/{id}_256s.jpg',model,out/f'review/{id}_oblique_0.png']):
   im=ImageOps.contain(Image.open(path).convert('RGB'),(690,488));x=col*700+(700-im.width)//2;y=row*540+45+(488-im.height)//2;canvas.paste(im,(x,y))
 canvas.save(tmp/f'final_review_{page+1:02}.jpg',quality=94)
canvas=Image.new('RGB',(2100,1660),'#eeeee7');d=ImageDraw.Draw(canvas)
for row,id in enumerate(['B007','B013']):
 y=row*830;d.text((16,y+6),id+(' · 三层修正为四层，并补充返程窗洞' if id=='B007' else ' · 装修住宅修正为砖混毛坯房'),font=font,fill='#283b3a')
 old=root/f'outputs/rectangular-photo-refinement/source_review/{id}_source_view.png';shutil.copy2(old,out/f'reference/{id}_previous_model.png')
 for col,(path,label) in enumerate([(out/f'reference/{id}_256s.jpg','返程原图 · 用于纠正判断'),(old,'上一版模型 · 去程机位'),(out/f'review/{id}_source_view.png','本次模型 · 去程机位')]):
  x=col*700;d.text((x+15,y+47),label,font=small,fill='#526661');im=ImageOps.contain(Image.open(path).convert('RGB'),(690,733));canvas.paste(im,(x+(700-im.width)//2,y+80+(733-im.height)//2))
canvas.save(out/'Revision_Highlights.jpg',quality=95)
p=out/'Village_Review.html';s=p.read_text().replace('<h2>去程 · 44 秒</h2>','<h2>两处可直接核对的修正</h2><a href="Revision_Highlights.jpg"><img class="hero" src="Revision_Highlights.jpg" alt="四层灰楼和毛坯房的返程证据与修改前后对照"></a><h2>去程 · 44 秒</h2>');p.write_text(s)
print('VISUAL_CHECK_SHEETS_READY')
