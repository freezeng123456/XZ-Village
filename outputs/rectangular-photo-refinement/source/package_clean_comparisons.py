"""Publish separated source-photo and pure-model panels; never composite source pixels into renders."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import shutil
root=Path.cwd();out=root/'outputs/rectangular-photo-refinement';refs=out/'reference';refs.mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',34);small=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',25)
for t,name in [(44,'Architecture_44s.png'),(256,'Architecture_Return_256s.png')]:
 src=root/f'work/buildings/source_{t}_4k.jpg';ref=refs/f'Source_{t}s.jpg'
 if src.exists():shutil.copy2(src,ref)
 canvas=Image.new('RGB',(3240,1035),'#ecece5');d=ImageDraw.Draw(canvas);d.text((20,14),f'原视频画面 · {t} 秒',font=font,fill='#26363a');d.text((1640,14),'纯模型渲染 · 无照片铺底／无照片纹理',font=font,fill='#26363a')
 for x,p in [(0,ref),(1640,out/name)]:canvas.paste(ImageOps.fit(Image.open(p).convert('RGB'),(1600,900)),(x,75))
 d.text((20,994),'分栏对照：原图与模型分别展示；模型机位对应原视频，几何和镜头估计仍存在偏差。',font=small,fill='#40535a');canvas.save(out/f'Scene_Comparison_{t}s.jpg',quality=94)
p=out/'Village_Review.html';s=p.read_text();s=s.replace('住宅方正，外观逐栋细化','纯模型与原图，分栏对照').replace('XZ Village · 矩形建筑与照片细化','XZ Village · 纯模型照片对照');s=s.replace('保留红框基准建筑，新增逐栋建筑模型。','模型已移除照片地面、立面照片覆层和相机背景图，只展示实际建出的结构与材质。原视频仅出现在独立的参考栏。');s=s.replace('道路、地形和植物为背景近似；','模型图没有照片背景或地面投影；');s=s.replace('<img class="overview" src="Architecture_44s.png" alt="整村模型全景">','<a href="Scene_Comparison_44s.jpg" target="_blank"><img class="overview" src="Scene_Comparison_44s.jpg" alt="44 秒原图与纯模型分栏对照"></a><nav><a href="Architecture_44s.png">单独查看纯模型</a><a href="Scene_Comparison_256s.jpg">256 秒原图与纯模型对照</a><a href="Whole_Village.png">纯模型全范围</a></nav>');p.write_text(s)
print('SEPARATE_PHOTO_MODEL_PANELS_READY')
