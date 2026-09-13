from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
p=Path('work/rebuild4/architecture');bs=json.loads((p/'village_mesh_input.json').read_text())['entries'];font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',23)
for pg in range(1,27):
 src=p/f'final_gallery/geometry_{pg:02}.png';out=p/f'final_gallery/geometry_{pg:02}.jpg'
 if not src.exists():continue
 im=Image.open(src).convert('RGB');dr=ImageDraw.Draw(im)
 for j,b in enumerate(bs[(pg-1)*16:pg*16]):
  x=j%4*600+10;y=j//4*300+8;dr.rounded_rectangle((x-4,y-3,x+116,y+28),4,fill='#e8eee9');dr.text((x,y),b['id'],font=font,fill='#25373b')
 im.save(out,quality=93)
