"""Make a self-contained, source-separated review and reproducible model delivery."""
import json,shutil,hashlib,html,csv
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
root=Path.cwd();out=root/'outputs/orthogonal-multiview';data=root/'work/buildings/v3';fontpath='/System/Library/Fonts/STHeiti Medium.ttc'
font=ImageFont.truetype(fontpath,30);small=ImageFont.truetype(fontpath,22);out.joinpath('reference').mkdir(exist_ok=True)
for f in ['inventory.json','profiles.json','multiview_changes.json']:shutil.copy2(data/f,out/f)
bs={b['id']:b for b in json.loads((data/'inventory.json').read_text())['buildings']};changes=json.loads((data/'multiview_changes.json').read_text());ids=sorted(set(c['id'] for c in changes));manifest=json.loads((data/'multiview_review_manifest.json').read_text())
print(type(manifest).__name__)
if isinstance(manifest,list):manifest={m['id']:m for m in manifest}
for t in [44,252,256,260,264]:
 source=(root/f'work/buildings/source_{t}_4k.jpg') if t==44 else data/f'source_{t}_4k.jpg';shutil.copy2(source,out/f'reference/Source_{t}s.jpg')
for t,name in [(44,'Architecture_44s.png'),(256,'Architecture_Return_256s.png')]:
 canvas=Image.new('RGB',(3240,1035),'#ecece5');d=ImageDraw.Draw(canvas);d.text((20,15),f'原视频 · {t} 秒',font=font,fill='#26363a');d.text((1640,15),'修订模型 · 实际几何与材质',font=font,fill='#26363a')
 for x,path in [(0,out/f'reference/Source_{t}s.jpg'),(1640,out/name)]:canvas.paste(ImageOps.fit(Image.open(path).convert('RGB'),(1600,900)),(x,75))
 d.text((20,994),'原图与模型分栏展示；镜头、建筑尺寸及遮挡部分仍有估计误差。模型内无照片地面、立面照片或相机背景。',font=small,fill='#40535a');canvas.save(out/f'Scene_Comparison_{t}s.jpg',quality=94)
# Label the complete opposing-view atlas with persistent building IDs.
gal=json.loads((out/'gallery/gallery_manifest.json').read_text())
for page in sorted(set(r['page'] for r in gal)):
 im=Image.open(out/f'gallery/geometry_{page:02}.png').convert('RGB');d=ImageDraw.Draw(im)
 for row in [r for r in gal if r['page']==page]:
  x=row['column']*600+16;y=row['row']*300+10;d.rounded_rectangle((x-5,y-3,x+83,y+30),5,fill='#eef0e9');d.text((x,y),row['id'],font=small,fill='#26363a')
 im.save(out/f'gallery/geometry_{page:02}.jpg',quality=92)
# Keep reference crops unaltered. Projection overlays are work-only diagnostics.
for id in ids:
 for time_key,v in manifest[id]['views'].items():
  t=int(time_key);bbox=v['crop_1600'];roof=v['roof_px'];cx=sum(p[0] for p in roof)/len(roof);cy=sum(p[1] for p in roof)/len(roof)
  if not (0<=cx<=1600 and 0<=cy<=900):continue
  src=Image.open(out/f'reference/Source_{t}s.jpg');scale=src.width/1600;box=[round(x*scale) for x in bbox]
  if box[0]>=src.width or box[2]<=0 or box[1]>=src.height or box[3]<=0:continue
  box=[max(0,box[0]),max(0,box[1]),min(src.width,box[2]),min(src.height,box[3])]
  if box[2]>box[0] and box[3]>box[1]:src.crop(box).save(out/f'reference/{id}_{t}s.jpg',quality=95)
words={
'B007':'返程显示四层；增加背面成对窗、小窗与空调，修正屋顶直角缺角。',
'B008':'修正转角缺口，并区分阳台正面与返程背面窗洞。',
'B009':'保留浅绿色正面，背侧改为褪色灰白墙，减少重复窗洞。',
'B010':'加入浅缺角；返程侧改为每层单窗与较轻的灰白旧墙。',
'B012':'恢复直角缺口、转角阳台及背面的双窗布局。',
'B013':'按返程毛坯房修改：裸砖、混凝土框架、空窗洞，移除假阳台及玻璃。',
'B019':'按返程减少背面窗户，恢复大面积素墙。',
'R001':'墙面恢复低饱和棕色砖面。','R002':'修正灰色小砖墙与暗红檐口；后侧屋顶延伸仍待更可靠定位。',
'R007':'旧墙改为深灰色，并补齐返程上层一排六扇窗。','R008':'旧墙色调与相邻老屋协调，保留独立屋顶单元。',
'R009':'恢复蓝色平屋顶防水层。','R010':'恢复较暗的红褐色露台铺面。','R013':'恢复红褐色露台铺面，区分中央小窗与两侧大窗。',
'R017':'补建返程可见的浅蓝色露台棚及细支柱。','R021':'恢复灰白色大面积素墙，保留较低位置的小窗。','R022':'将墙面调整为淡米灰色。'}
esc=html.escape
cards=[]
for id in ids:
 pics=[]
 for t in [44,256]:
  path=f'reference/{id}_{t}s.jpg'
  if (out/path).exists():pics.append(f'<figure><a href="{path}" target="_blank"><img loading="lazy" src="{path}" alt="{id} {t} 秒原图"></a><figcaption>{t} 秒原视频局部</figcaption></figure>')
 for suffix,label in [('source_view','主要参考估计机位'),('return_view','返程估计机位'),('oblique_0','模型正面斜视'),('oblique_1','模型背面斜视')]:
  path=f'review/{id}_{suffix}.png'
  if (out/path).exists():pics.append(f'<figure><a href="{path}" target="_blank"><img loading="lazy" src="{path}" alt="{id} {label}"></a><figcaption>{label}</figcaption></figure>')
 cards.append(f'<article data-id="{id}"><h3>{id} · {esc(bs[id]["name"])}</h3><p>{words[id]}</p><div class="images">'+''.join(pics)+'</div></article>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>XZ Village · 去返程共同修订</title><style>
*{box-sizing:border-box}body{margin:0;background:#eaece5;color:#263638;font:16px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1500px;margin:auto;padding:36px}h1{font-size:36px;line-height:1.25}h2{margin-top:44px}p{max-width:1120px}a{color:#24675e}nav{display:flex;gap:20px;flex-wrap:wrap;margin:24px 0}img{display:block;width:100%}.hero{border-radius:12px;background:#263638}.callout{background:#fffdf3;padding:18px 24px;border-left:4px solid #91774f}article{background:#fafbf6;padding:20px;margin:24px 0;border-radius:12px}.images{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}figure{margin:0;background:#e7e9e1;border-radius:8px;overflow:hidden}.images img{height:330px;object-fit:contain;background:#30383a}figcaption{padding:8px 12px;font-size:14px}input{width:300px;max-width:100%;padding:12px;border:1px solid #aab8ae;border-radius:6px;font:inherit}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.gallery img{border-radius:8px}footer{padding:30px 0;font-size:14px;color:#5c6c65}@media(max-width:800px){main{padding:18px}.images,.gallery{grid-template-columns:1fr}h1{font-size:28px}.images img{height:auto}}
</style><main><p>XZ VILLAGE / MULTIVIEW REVISION</p><h1>去返程共同修订：直角轮廓与分面材质</h1><p>保留基准建筑与 297 个编号重建单元。四栋近景住宅采用有直角缺口的平面；17 个单元有明确的返程修正，其余单元更新材质、檐口、窗套和瓦片表现。编号包含屋顶与侧翼单元，并非 298 户住宅的统计。</p><nav><a href="Village_Multiview_Refined.blend">下载 Blender 模型</a><a href="#detail">17 个重点修订</a><a href="#all">全部 297 单元双面图册</a><a href="RECONSTRUCTION_REPORT.md">修改与检验说明</a></nav><div class="callout">照片仅用于下方独立参考栏。模型内没有照片铺地、立面照片覆层或相机背景。直角约束针对墙体平面；坡屋顶保留坡度。尺寸、缺角向底层的延伸、被遮挡的门窗仍属估计。</div><h2>去程 · 44 秒</h2><a href="Scene_Comparison_44s.jpg"><img class="hero" src="Scene_Comparison_44s.jpg" alt="去程原视频与修订模型分栏对照"></a><h2>返程 · 256 秒</h2><a href="Scene_Comparison_256s.jpg"><img class="hero" src="Scene_Comparison_256s.jpg" alt="返程原视频与修订模型分栏对照"></a><nav><a href="Architecture_44s.png">去程纯模型</a><a href="Architecture_Return_256s.png">返程纯模型</a><a href="Whole_Village.png">全范围模型</a><a href="Geometry_Overview.png">中性材质几何检查</a></nav><h2 id="detail">17 个重点修订</h2><p>点击图片可放大。正反斜视用于检查结构，不与原图作像素级重合。返程镜头采用既有手工控制点估计，尚未完成去返程统一摄影测量校准。</p><label>查找建筑 <input aria-label="查找建筑" placeholder="例如 B007、R021"></label>'''+''.join(cards)+'''<h2 id="all">全部 297 单元双面图册</h2><p>每组编号含正反两个方向，同一模型、同一材质。图册覆盖所有单元；完整图册检查与近景逐张检查的范围见检验说明。</p><div class="gallery">'''+''.join(f'<a href="gallery/geometry_{i:02}.jpg"><img loading="lazy" src="gallery/geometry_{i:02}.jpg" alt="第 {i} 页建筑双面图册"></a>' for i in range(1,20))+'''</div><footer>版本：2026-09-13 · 本地保存并从交付文件重新检查。具体事实、估计和未验证项目见随附报告。</footer></main><script>document.querySelector('input').addEventListener('input',e=>{const q=e.target.value.trim().toUpperCase();document.querySelectorAll('article').forEach(a=>a.hidden=!a.dataset.id.includes(q));});</script></html>'''
for i in range(1,20):
 names=' '.join(r['id'] for r in gal if r['page']==i)
 page=page.replace(f'<a href="gallery/geometry_{i:02}.jpg">',f'<a data-ids="{names}" href="gallery/geometry_{i:02}.jpg">')
page=page.replace("document.querySelectorAll('article').forEach(a=>a.hidden=!a.dataset.id.includes(q));","document.querySelectorAll('article').forEach(a=>a.hidden=!a.dataset.id.includes(q));document.querySelectorAll('.gallery a').forEach(a=>a.hidden=!a.dataset.ids.includes(q));")
(out/'Village_Review.html').write_text(page)
print('V3_REVIEW_PACKAGED',len(cards))
