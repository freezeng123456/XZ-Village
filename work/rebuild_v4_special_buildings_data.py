"""Source-reviewed public structures and a traditional compound, kept individually editable."""
import json,copy,numpy as np
from pathlib import Path
from scipy.optimize import least_squares
from rebuild_v4_arch_geometry import intersect_z,project
from rebuild_v4_orthogonal_fit import orthogonal_outline
P=Path('work/rebuild4/architecture');gd=json.loads((P/'village_mesh_input.json').read_text());g={b['id']:b for b in gd['entries']};pd=json.loads((P/'village_profiles.json').read_text());p={b['id']:b for b in pd['entries']};audit=[]
def outline(bid,sec,poly,z):
 b=g[bid];vv,fit=orthogonal_outline(poly,f'frame_{sec:06.2f}.jpg',z);b.update(footprint_world=vv[:,:2].tolist(),roof_edge_height=z,fit=fit,source_polygon_px=poly,source_image=f'frame_{sec:06.2f}.jpg',geometry_method='manually traced source-specific form and orthogonal fit at source-supported height');audit.append(dict(id=bid,source_image=b['source_image'],polygon_px=poly,fit=fit));return b
# Main hall and its visibly separated rear gate are not one giant pitched block.
b=outline('V0111',256,[[954,684],[1102,686],[1096,766],[950,764]],5.686);b['special_model']='curved_ridge_hall';b['ridge_height']=8.744;b['roof_type']='gable'
if 'V0111G' not in g:g['V0111G']=copy.deepcopy(b);p['V0111G']=copy.deepcopy(p['V0111']);g['V0111G'].update(id='V0111G',name='Traditional hall rear gate',source_ids=['V0111'],parent_id='V0111',source_role='gate');p['V0111G']['id']='V0111G'
b=outline('V0111G',256,[[1001,647],[1071,646],[1069,668],[998,669]],6.35);b.update(special_model='curved_ridge_gate',ridge_height=8.4)
for bid in ['V0111','V0111G']:
 p[bid].update(color=[.45,.44,.39],style='plaster',roof_color=[.53,.31,.24],wall_age=.72,roof_age=.64,faces={str(i):dict(openings=[],balconies=[],equipment=[]) for i in range(4)})
# Stage: freestanding enclosed wings flank a large recessed performance opening.
g['V0024']['special_model']='open_stage';g['V0024']['front_face']=2;g['V0024']['roof_type']='hip_metal';p['V0024'].update(color=[.57,.24,.22],roof_color=[.80,.27,.22])
# Six-sided pavilion. The former mask selected an L-shaped patch of the roof.
q=intersect_z([[1467,404],[1477,410],[1493,413],[1509,410],[1519,405],[1507,399],[1480,398]],'frame_064.00.jpg',3.9166)[:,:2];center=np.mean(q,0);fit=least_squares(lambda v:np.linalg.norm(q-v[:2],axis=1)-v[2],np.r_[center,3.1]);center=fit.x[:2];radius=float(np.clip(fit.x[2],2.5,4.2));xy=center+np.column_stack([np.cos(np.arange(6)*np.pi/3),np.sin(np.arange(6)*np.pi/3)])*radius
g['V0493'].update(footprint_world=xy.tolist(),special_model='six_column_pavilion',roof_edge_height=3.9166,ridge_height=6.05,floor_count=1,geometry_method='six-sided open pavilion from native source silhouette',pavilion_radius=radius);p['V0493'].update(roof_color=[.62,.26,.23],color=[.77,.76,.68])
# Long public building has two storeys and one red raised centre roof.
for bid,poly,z,typ in [('V0490',[[1385,268],[1497,263],[1500,282],[1393,286]],8.0,'flat'),('V0491',[[1498,265],[1599,260],[1601,281],[1501,285]],8.4,'gable'),('V0492',[[1600,263],[1680,265],[1681,280],[1601,284]],8.0,'flat')]:
 b=outline(bid,64,poly,z);b.update(roof_type=typ,floor_count=2,base_height=-.9746,ridge_height=10.19 if typ=='gable' else z,special_form='two-storey public building, source traced roof and frontage')
 pr=p[bid];pr.update(color=[.79,.68,.67],roof_color=[.68,.37,.34] if typ=='gable' else [.41,.41,.40],glazing_color=[.17,.41,.41],style='plaster',wall_age=.28,faces={})
 xy=np.array(b['footprint_world']);uv=project(np.column_stack([xy,np.full(len(xy),z)]),'frame_064.00.jpg');longedges=np.linalg.norm(np.roll(xy,-1,axis=0)-xy,axis=1);candidates=np.argsort(longedges)[-2:];front=max(candidates,key=lambda j:np.mean(uv[[j,(j+1)%4],1]));b['front_face']=int(front)
 for j in range(4):
  f=dict(openings=[],balconies=[],equipment=[],color=[.79,.68,.67],style='plaster',annotation_status='manual public-building source facade',floor_bands=True,accent_color=[.84,.66,.68]);pr['faces'][str(j)]=f
  if j==front:
   centers=[.11,.245,.39,.55,.69,.84] if bid=='V0490' else ([.10,.22,.36,.64,.77,.90] if bid=='V0491' else [.13,.30,.47,.66,.84]);f['public_facade']=True;f['ornamental_pilasters']=[.012,.988];f['public_crest']=typ=='flat'
   for y in [.25,.73]:
    for x in centers:f['openings'].append(dict(box=[x-.047,y-.092,x+.047,y+.092],kind='window',inferred=y>.5,source_method='manual public-building window row; lower portions partly tree-occluded'))
   if bid=='V0491':f['openings'].append(dict(box=[.44,.12,.59,.47],kind='empty',inferred=False))
# Boundary patch belongs to the pink house's lower balcony, not an independent house.
gd['unresolved']=[u for u in gd.get('unresolved',[]) if u['id']!='V0473'];gd.setdefault('component_adjudications',{})['V0473']=dict(status='attached balcony surface of V0472',parent_id='V0472',source_image='frame_090.00.jpg',evidence='native source crop shows continuous balcony slab below the pink upper storey, partly beyond image boundary')
g['V0472']['source_ids']=sorted(set(g['V0472'].get('source_ids',[])+['V0473']));g['V0472']['floor_count']=3
# Save all modifications without resetting the separate hand-annotated houses.
gd['entries']=list(g.values());pd['entries']=list(p.values());(P/'village_mesh_input.json').write_text(json.dumps(gd,ensure_ascii=False));(P/'village_profiles.json').write_text(json.dumps(pd,ensure_ascii=False));(P/'special_buildings_audit.json').write_text(json.dumps(audit,indent=2));print('SPECIAL BUILDINGS',len(audit),'pavilion radius',radius)
