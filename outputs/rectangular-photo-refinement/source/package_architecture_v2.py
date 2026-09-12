"""Build source-camera comparison cards, offline review and evidence report for V2."""
from pathlib import Path
import json,html,shutil,csv,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
root=Path.cwd();out=root/'outputs/rectangular-photo-refinement';review=out/'review';cards=review/'buildings';cards.mkdir(exist_ok=True);bs=json.loads((root/'work/buildings/v2/inventory.json').read_text())['buildings'];profiles=json.loads((root/'work/buildings/v2/profiles.json').read_text());manifest={m['id']:m for m in json.loads((out/'source_review/source_view_manifest.json').read_text())};font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',25);small=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',19);cache={};atlases={};entries=[];allcards=[]
def fit(im,size):
 canvas=Image.new('RGB',size,'#283135');im=ImageOps.contain(im,size,Image.Resampling.LANCZOS);canvas.paste(im,((size[0]-im.width)//2,(size[1]-im.height)//2));return canvas
for i,b in enumerate(bs):
 bid=b['id'];m=manifest[bid];t=str(m['source_time'])
 if t not in cache:
  p=root/f'work/buildings/source_{t}_4k.jpg';cache[t]=Image.open(p if p.exists() else root/m['source_image'])
 im=cache[t];scale=im.width/1600;crop=im.crop(tuple(round(x*scale) for x in m['source_crop_1600']));outline=(np.array(b['roof'])*scale-np.array(m['source_crop_1600'][:2])*scale).tolist();draw_source=ImageDraw.Draw(crop);draw_source.line([tuple(q) for q in outline+[outline[0]]],fill=(240,173,65),width=max(1,round(crop.width/350)));render=Image.open(out/'source_review'/f'{bid}_source_view.png');page=i//16+1;idx=i%16
 if page not in atlases:atlases[page]=Image.open(review/f'geometry_{page:02}.png')
 x=idx%4*600;y=idx//4*300;opposite=atlases[page].crop((x+300,y,x+600,y+300))
 card=Image.new('RGB',(1400,620),'#edece5');card.paste(fit(crop,(500,535)),(0,65));card.paste(fit(render,(500,535)),(500,65));card.paste(fit(opposite,(400,535)),(1000,65));d=ImageDraw.Draw(card);d.text((15,7),bid+' · '+b['name'],font=font,fill='#243339');d.text((15,39),'照片参考 · '+t+' 秒 · 黄线标示屋顶',font=small,fill='#4b5b60');d.text((515,39),'模型 · 对应照片视角',font=small,fill='#4b5b60');d.text((1015,39),'模型 · 背面检查',font=small,fill='#4b5b60');d.text((15,600),'矩形主体；可见外观参考照片，遮挡面与细节合理补全。',font=small,fill='#4b5b60');card.save(cards/f'{bid}.jpg',quality=91);allcards.append(card)
 r=b['rectangle'];entries.append(dict(id=bid,name=b['name'],type=b['type'],source_seconds=b['t'],width_m=r['width'],depth_m=r['depth'],source_roof_iou=r['source_roof_iou_after_placement'],source_edge_rmse_px=r['source_edge_rmse_px_after_placement'],near_source_review=profiles[bid]['manual_source_review'],review_image=f'review/buildings/{bid}.jpg',inference='隐蔽面、远景细部、层高和尺寸为合理推测'))
for page in range((len(allcards)+11)//12):
 canvas=Image.new('RGB',(1400,1860),'#edece5')
 for j,card in enumerate(allcards[page*12:(page+1)*12]):canvas.paste(card.resize((700,310),Image.Resampling.LANCZOS),(j%2*700,j//2*310))
 canvas.save(review/f'comparison_{page+1:02}.jpg',quality=90)
# A larger near-field contact sheet is also a convenient one-file preview.
hero=Image.new('RGB',(1400,1860),'#edece5')
for j,bid in enumerate(['B005','B008','B010']):hero.paste(Image.open(cards/f'{bid}.jpg'),(0,j*620))
hero.save(out/'Photo_Model_Comparison.jpg',quality=94)
(out/'building_inventory.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2))
with (out/'building_inventory.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(entries[0]));w.writeheader();w.writerows(entries)
items=''.join('<article data-search="'+html.escape(e['id']+' '+e['name']+' '+e['type'])+'"><a href="'+e['review_image']+'" target="_blank"><img loading="lazy" src="'+e['review_image']+'" alt="'+html.escape(e['id']+' 照片与模型对照')+'"></a><div><b>'+e['id']+' · '+html.escape(e['name'])+'</b><span>'+str(e['source_seconds'])+' 秒参考 · '+e['type']+' · 矩形主体</span></div></article>' for e in entries)
old=(root/'outputs/building-quality/Village_Review.html').read_text();head=old.split('<div class="grid">')[0];head=head.replace('XZ Village · 逐栋重建','XZ Village · 矩形建筑与照片细化').replace('整村建筑，逐栋可查看','住宅方正，外观逐栋细化').replace('Village_Reconstructed.blend','Village_Rectangular_Refined.blend').replace('每张卡片左侧为视频参考，中间与右侧为同一模型的正面和背面斜视图。','每张卡片左侧为照片参考，中间为对应照片视角的模型，右侧为模型背面。').replace('建筑轮廓与布局参考视频；',f'本轮 {len(bs)} 个重建单元采用矩形主体；{sum(p["manual_source_review"] for p in profiles.values())} 个单元使用单独的照片外观修订配置。原 O069、R031 是露天空地，已剔除。建筑布局参考视频；').replace('无照片材质的结构检查','结构检查').replace('视频编号覆盖图','参考视频编号图')
head=head.replace('Whole_Village.png','Architecture_44s.png')
foot=old.split('</div><footer>',1)[1];foot=foot.replace('双向模型预览','照片视角与背面预览');(out/'Village_Review.html').write_text(head+'<div class="grid">'+items+'</div><footer>'+foot)
for name in ['Coverage_44s.jpg','Coverage_20s.jpg','Coverage_Return_256s.jpg','Landmark_Original.png']:
 shutil.copy2(root/'outputs/building-quality'/name,out/name)
for name in ['final_alignment_audit.json','rectangle_fit_audit.json','placement_corrections.json','rejected_candidates.json','inventory.json','profiles.json']:
 shutil.copy2(root/'work/buildings/v2'/name,out/name)
print('PACKAGED_COMPARISONS',len(entries),'pages',(len(entries)+11)//12)
