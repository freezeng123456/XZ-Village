"""Final cross-frame duplicate adjudication, retaining every original component id."""
import json,numpy as np
from pathlib import Path
from rebuild_v4_orthogonal_fit import orthogonal_outline
P=Path('work/rebuild4/architecture');gd=json.loads((P/'village_mesh_input.json').read_text());pd=json.loads((P/'village_profiles.json').read_text());g={b['id']:b for b in gd['entries']};p={b['id']:b for b in pd['entries']};audit=[]
for filename in ['village_mesh_input.json','village_profiles.json']:
 bk=P/(filename+'.before_final_dedup');
 if not bk.exists():bk.write_bytes((P/filename).read_bytes())
def outline(k,pixels,fr=256,z=None,typ=None,blank=False):
 b=g[k];z=b['roof_edge_height'] if z is None else z;v,fit=orthogonal_outline(pixels,f'frame_{fr:03}.00.jpg',z);b.update(footprint_world=v[:,:2].tolist(),roof_edge_height=z,source_polygon_px=pixels,source_image=f'frame_{fr:03}.00.jpg',fit=fit,geometry_method='final native-source outline adjudication after world-overlap review')
 if typ:b['roof_type']=typ
 if blank:p[k]['faces']={str(j):dict(openings=[],balconies=[],equipment=[],style=p[k].get('style','plaster'),color=p[k].get('color',[.55,.56,.52]),annotation_status='source wall obscured; detailed openings not established') for j in range(len(v))}
 audit.append(dict(id=k,action='refit source roof perimeter',frame=fr,rms_px=fit['rms_px'],roof_type=b['roof_type']))
def merge(parent,child,reason):
 if child not in g:return
 g[parent]['source_ids']=list(dict.fromkeys(g[parent].get('source_ids',[parent])+g[child].get('source_ids',[child])))
 for b in g.values():
  if b.get('parent_id')==child:b['parent_id']=parent
 g.pop(child);p.pop(child);gd.setdefault('component_adjudications',{})[child]=dict(status='duplicate roof observation merged',parent_id=parent,reason=reason);audit.append(dict(id=child,action='merge duplicate',parent_id=parent,reason=reason))
outline('V0171',[[2345,126],[2241,135],[2282,181],[2396,176]],z=17.47)
merge('V0171','V0180','Same four-storey flat-roof house in native frame256, overlapping portions of the same continuous deck')
outline('V0193',[[2100,636],[2043,575],[1940,595],[1997,654]],typ='gable',blank=True)
g['V0193']['ridge_height']=10.35;p['V0193']['roof_color']=[.62,.36,.24]
merge('V0193','V0195','One broad orange tiled gable observed twice; metal label was a mistaken partial roof interpretation')
outline('V0200',[[2150,440],[2240,428],[2280,466],[2189,479]],fr=252,z=7.0,typ='flat',blank=True)
p['V0200']['roof_color']=[.75,.43,.32]
merge('V0200','V0201','Same continuous red terrace behind the large photovoltaic array, native frame252')
merge('V0234','V0233','Same long white prefabricated wing; full extent is visible in frame238')
outline('V0234',[[1750,1186],[1838,1241],[1809,1246],[1720,1188]],fr=238)
# Resolve the crowded compound into two tile strips and two red terrace appendices.
outline('V0204',[[2020,678],[2056,670],[2070,686],[2032,696]],typ='gable',blank=True)
outline('V0205',[[2061,664],[2099,655],[2121,674],[2082,685]],typ='flat',blank=True)
outline('V0206',[[1984,680],[2011,673],[2038,704],[2011,713]],typ='flat',blank=True)
outline('V0238',[[2011,665],[2044,658],[2054,668],[2021,676]],typ='gable',blank=True)
for k in ['V0204','V0238']:g[k]['ridge_height']=g[k]['roof_edge_height']+.75;p[k]['roof_color']=[.55,.33,.23]
for k in ['V0205','V0206']:p[k]['roof_color']=[.68,.42,.32]
outline('V0152',[[1096,1078],[1040,1074],[1026,1163],[1090,1168]],typ='gable',blank=True)
outline('V0154',[[1101,1041],[1053,1040],[1046,1074],[1096,1076]],typ='flat',blank=True)
g['V0160']['roof_type']='flat';p['V0160']['roof_color']=[.39,.41,.37]
audit.append(dict(id='V0160',action='gray flat courtyard roof corrected from gable',source_image='frame_256.00.jpg'))
# Identify broad overlaps that remain intentional based on original source inspection.
gd['overlap_adjudications']=[dict(ids=pair,status='source-confirmed attached wings or canopy overhang; footprint intersection does not imply duplicate') for pair in [['P004','V0097'],['V0028','V0421'],['V0030','V0032'],['V0060','V0061'],['V0139','V0148'],['V0156','V0157'],['V0160','V0161'],['V0194','V0196']]]
gd['entries']=list(g.values());pd['entries']=list(p.values());(P/'village_mesh_input.json').write_text(json.dumps(gd,ensure_ascii=False));(P/'village_profiles.json').write_text(json.dumps(pd,ensure_ascii=False));(P/'final_duplicate_adjudication.json').write_text(json.dumps(dict(entries=audit,units_after=len(g)),indent=2,ensure_ascii=False));print(json.dumps(dict(units=len(g),audit=audit),indent=2))
