"""Native-source visual adjudication of facade proposals, preserving manual special forms."""
import json,numpy as np
from pathlib import Path
P=Path('work/rebuild4/architecture');pd=json.loads((P/'village_profiles.json').read_text());p={b['id']:b for b in pd['entries']};gd=json.loads((P/'village_mesh_input.json').read_text());g={b['id']:b for b in gd['entries']};audit=[]
def face(bid,j,clear=True,color=None,style=None):
 bid=f'V{bid:04}' if isinstance(bid,int) else bid;f=p[bid]['faces'].setdefault(str(j),dict(openings=[],balconies=[],equipment=[]))
 if clear:f.update(openings=[],balconies=[])
 if color is not None:f['color']=color
 if style:f['style']=style
 f['annotation_status']='visually adjudicated source facade';audit.append(dict(id=bid,face=j,source_image=f.get('source_image'),review='source-visible geometry, openings and occlusions manually examined'));return f
def op(f,box,kind='window',inferred=False):f['openings'].append(dict(box=box,kind=kind,inferred=inferred,source_method='manual source facade adjudication'))
def rows(f,xs,ys,w,h,kind='window',inferred=False):
 for y in ys:
  for x in xs:op(f,[x-w/2,y-h/2,x+w/2,y+h/2],kind,inferred)
def log(f,x0,x1,floors,depth=1.0,rail='stone',arch=False,inferred=False):f['balconies'].append(dict(x0=x0,x1=x1,floors=floors,depth=depth,rail=rail,arch=arch,inferred=inferred,source_method='manual source facade adjudication'))
def floor(bid,n):g[f'V{bid:04}']['floor_count']=n;g[f'V{bid:04}']['floor_status']='visible rows and source facade manually counted'
def blank(items):
 for bid,j in items:face(bid,j)
# Pages 00-03 of the persisted source review gallery.
f=face(1,0);rows(f,[.19,.57,.90],[.18,.51],.26,.24)
blank([(2,2),(2,3),(4,2),(4,3),(6,3),(7,1),(10,0),(11,6),(12,5),(18,4),(19,0),(22,0),(26,3),(37,2),(37,0),(39,0),(41,3),(42,2),(43,3),(46,0),(46,3)])
f=face(3,2);op(f,[.30,.03,.44,.16])
f=face(8,0);floor(8,3);log(f,.02,.52,[1,2],1.0);rows(f,[.80],[.18,.49],.22,.16);op(f,[.65,.77,.93,.97],'door',True)
f=face(8,3,False);log(f,.06,.98,[1,2],1.2)
f=face(9,3);floor(9,3);log(f,.08,.92,[1,2],.75,'metal');rows(f,[.31,.78],[.12],.24,.18)
f=face(9,0);rows(f,[.26,.64],[.13,.55],.13,.20);rows(f,[.90],[.12],.11,.16)
f=face(10,2,False);f['annotation_status']='real side window rows verified; lower source occlusion retained'
f=face(13,3);rows(f,[.21,.55],[.20,.51],.18,.21);rows(f,[.19],[.80],.18,.15)
f=face(14,2);rows(f,[.115,.56],[.18],.12,.19);rows(f,[.57],[.57],.11,.19)
f=face(16,5);rows(f,[.28],[.115,.435],.13,.12);rows(f,[.60],[.225,.535,.845],.12,.12);rows(f,[.94],[.11,.47,.82],.14,.13)
f=face(16,4);rows(f,[.14,.83],[.16,.48],.17,.14);rows(f,[.14,.46,.83],[.84],.16,.14)
f=face(17,3);rows(f,[.19,.75],[.15,.47,.80],.22,.19)
f=face(18,3);op(f,[.32,.06,.40,.31]);op(f,[.86,.11,.91,.33])
f=face(19,3);rows(f,[.20,.68],[.18,.66],.18,.18)
f=face(21,3);rows(f,[.055,.345,.64,.935],[.145,.775],.046,.15)
f=face(21,0);rows(f,[.025,.50,.92],[.23],.075,.19)
f=face(26,2);op(f,[.82,.14,.96,.43])
f=face(35,4);op(f,[.41,.47,.50,.60])
f=face(43,2);rows(f,[.086,.62,.89],[.40],.065,.26)
f=face(44,2);rows(f,[.12,.83],[.12,.37],.11,.11)
f=face(45,2,False);p['V0045']['wall_age']=.65
f=face(47,0);op(f,[.31,.30,.72,.81]);op(f,[.82,.29,.91,.51]);floor(47,2)
# Additional source-reviewed pages are appended below before saving.
EXTRA=P/'manual_facade_adjudication_extra.py'
if EXTRA.exists():exec(EXTRA.read_text())
pd['entries']=list(p.values());gd['entries']=list(g.values());(P/'village_profiles.json').write_text(json.dumps(pd,ensure_ascii=False));(P/'village_mesh_input.json').write_text(json.dumps(gd,ensure_ascii=False));(P/'facade_adjudication_audit.json').write_text(json.dumps(audit,indent=2));print('ADJUDICATED FACES',len(audit))
