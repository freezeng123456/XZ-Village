"""Hand-adjudicated architectural profiles for distinctive source-visible homes.
Normalized measurements refer to the archived rectified face and native source view.
"""
import json,numpy as np
from pathlib import Path
P=Path('work/rebuild4/architecture');ppath=P/'village_profiles.json';pdoc=json.loads(ppath.read_text());p={v['id']:v for v in pdoc['entries']};gpath=P/'village_mesh_input.json';gdoc=json.loads(gpath.read_text());g={v['id']:v for v in gdoc['entries']};audit=[]
for v in p.values():
 if not v['id'].startswith('P'):v['equipment']=[e for e in v.get('equipment',[]) if e.get('provenance') not in ['compact elevated dense roof component','manual source fixture position']]
def face(bid,index,color=None,style=None):
 v=p[bid]['faces'].setdefault(str(index),dict(openings=[],balconies=[],equipment=[]));v.update(openings=[],balconies=[],equipment=[],annotation_status='manually measured from current source rectification')
 if color:v['color']=color
 if style:v['style']=style
 audit.append(dict(id=bid,face=index,source=v.get('source_image','source frame and gallery'),review='manual geometric opening and architectural form annotation'));return v
def opening(f,box,kind='window',inferred=False):f['openings'].append(dict(box=box,kind=kind,inferred=inferred,source_method='manual source measurement'))
def row(f,xs,ys,width,height,kind='window',inferred=False):
 for y in ys:
  for x in xs:opening(f,[x-width/2,y-height/2,x+width/2,y+height/2],kind,inferred)
def loggia(f,x0,x1,levels,depth=1.0,stone=True,arch=False,inferred=False):f['balconies'].append(dict(x0=x0,x1=x1,floors=levels,depth=depth,rail='stone' if stone else 'metal',arch=arch,inferred=inferred,source_method='manual source appearance and opening span'))

ivory=[.80,.80,.76];gray=[.64,.65,.64];cream=[.86,.84,.75]
f=face('V0480',0,ivory,'ceramic');row(f,[.26],[.13,.38,.64],.25,.14);loggia(f,.53,.96,[1,2,3],1.5,True,inferred=True);opening(f,[.18,.80,.42,.98],'door',True)
f=face('V0480',3,ivory,'ceramic');row(f,[.405,.615,.910],[.075,.345],.12,.135);row(f,[.41,.75],[.65],.13,.14)
f=face('V0481',3,[.76,.78,.75],'ceramic');row(f,[.36],[.185,.45,.69],.19,.15);row(f,[.78],[.45],.22,.15);loggia(f,.66,.98,[3],1.3,True)
f=face('V0481',4,[.75,.77,.74],'ceramic');row(f,[.75],[.20,.465,.735],.28,.18);loggia(f,.04,.59,[1,2,3],1.5,True);opening(f,[.10,.82,.52,.98],'door');f['floor_bands']=True;f['accent_color']=[.55,.31,.29]
f=face('V0482',0,[.60,.35,.28],'brick');loggia(f,.02,.50,[0,1,2],1.2,False);opening(f,[.65,.05,.95,.24],'empty');f['concrete_frame']=True
f=face('V0482',1,[.61,.36,.27],'brick');row(f,[.355,.76],[.14,.435],.17,.17,'empty');row(f,[.76],[.73],.17,.17,'empty');f['concrete_frame']=True
p['V0482']['style']='brick';p['V0482']['color']=[.61,.36,.27];p['V0482']['wall_age']=.4
f=face('V0483',0,[.88,.84,.70],'ceramic');loggia(f,.47,.96,[1,2],1.85,True,True);row(f,[.23],[.20,.455],.31,.19);opening(f,[.04,.62,.40,.95],'door');opening(f,[.53,.73,.90,.97],'door');f['ornamental_pilasters']=[.025,.435,.98];f['floor_bands']=True;f['accent_color']=[.90,.89,.82];f['front_awning']=dict(x0=.01,x1=.44,height=.37,depth=2.0,color=[.18,.40,.51])
f=face('V0483',3,[.82,.80,.73],'plaster');row(f,[.36],[.20,.46],.105,.13);row(f,[.20,.37,.64,.80],[.76],.105,.12)
p['V0483']['color']=[.86,.84,.73];p['V0483']['roof_color']=[.89,.89,.85];p['V0483']['wall_age']=.18;p['V0483']['glazing_color']=[.11,.31,.39]
g['V0484']['floor_count']=3;g['V0484']['floor_status']='three visible facade levels established from curved bay and balcony source view'
f=face('V0484',1,[.77,.81,.81],'ceramic');loggia(f,.03,.98,[1,2],1.4,True,True);opening(f,[.14,.72,.86,.98],'door');f['floor_bands']=True;f['accent_color']=[.62,.37,.32]
f=face('V0484',5,[.78,.82,.82],'ceramic');f['curved_stair_bay']=dict(sag=.72,window_x0=.27,window_x1=.73,window_bottom=.09,window_top=.92);p['V0484']['glazing_color']=[.075,.12,.12]
f=face('V0484',4,[.76,.79,.78],'plaster');row(f,[.51],[.17,.455],.095,.11);row(f,[.21,.52],[.76],.11,.13);row(f,[.35],[.41,.66],.03,.11)
p['V0484']['roof_color']=[.89,.90,.87];p['V0484']['wall_age']=.23
f=face('V0485',0,[.50,.51,.50],'plaster');opening(f,[.38,.17,.53,.25]);f['floor_bands']=True;f['ornamental_pilasters']=[.025,.98]
face('V0485',3,[.52,.53,.52],'plaster');p['V0485']['color']=[.50,.51,.50];p['V0485']['roof_color']=[.39,.42,.43];p['V0485']['wall_age']=.15
f=face('V0486',2,[.49,.51,.52],'plaster');row(f,[.18,.84],[.765],.25,.27);opening(f,[.41,.66,.62,.99],'door');opening(f,[.735,.185,.95,.455]);opening(f,[.055,.19,.345,.47]);loggia(f,.40,.635,[1],.82,True);f['bay_windows']=[dict(x0=.055,x1=.345,bottom=.52,top=.82,depth=.58)];f['ornamental_pilasters']=[.02,.38,.66,.98];f['floor_bands']=True;f['accent_color']=[.87,.87,.81]
face('V0486',3,[.52,.54,.54],'plaster');p['V0486']['color']=[.50,.52,.52];p['V0486']['roof_color']=[.89,.88,.83];p['V0486']['wall_age']=.18;p['V0486']['equipment']=[dict(type='pergola',xy=[.52,.50],width=2.65,depth=2.2,height=2.55)]
# Recover a bounded hidden portion at the two frame edges from the visible roof orientation.
from rebuild_v4_orthogonal_fit import orthogonal_outline
for bid,sec,poly,z,base in [('V0501',120,[[-90,440],[55,438],[101,409],[-36,411]],26.0,14.0),('V0356',0,[[-61,839],[77,839],[118,791],[-26,791]],17.39,8.11)]:
 vv,fit=orthogonal_outline(poly,f'frame_{sec:06.2f}.jpg',z);g[bid].update(footprint_world=vv[:,:2].tolist(),base_height=base,fit=fit,geometry_method='visible edge direction with explicitly inferred extension beyond image boundary',boundary_extent_inferred=True)
 g[bid].update(roof_edge_height=z,observed_roof_surface_height=z-.30,ridge_height=z)
g['V0501']['height_evidence']='Three visible floors and image vertical extent with 12-unit height prior; absolute height uncertain, earlier texture-poor 54-unit proposal rejected'
f=face('V0501',1,[.67,.34,.29],'ceramic');row(f,[.31],[.28,.59],.18,.20);row(f,[.78],[.13,.43,.63],.11,.11)
f=face('V0501',0,[.67,.34,.29],'ceramic');loggia(f,.02,.68,[1,2],1.0,True);opening(f,[.14,.75,.53,.98],'door');p['V0501']['color']=[.67,.34,.29]
# All proposed fixture positions remain traceable to compact elevated dense components.
fixtures=json.loads((P/'source_roof_fixtures.json').read_text())
excluded={'V0171','V0327','V0506'}
for e in fixtures:
 bid=e['id']
 if bid not in p or bid in excluded:continue
 b=g[bid];xy=np.array(b['footprint_world']);ang=np.arctan2(*(xy[1]-xy[0])[::-1]);R=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]]);local=(xy-xy.mean(0))@R;q=(np.array(e['center_world'])-xy.mean(0))@R;norm=(q-local.min(0))/np.maximum(.01,np.ptp(local,axis=0));ee={k:v for k,v in e.items() if k in ['type','radius','height','stand']};ee.update(xy=norm.tolist(),provenance='compact elevated dense roof component',source_points=e['source_points']);p[bid].setdefault('equipment',[]).append(ee)
# Individually source-located fixtures on the northern architectural comparison row.
from rebuild_v4_arch_geometry import intersect_z
def fixture(bid,sec,px,typ='tank',h=1.35,rad=.48):
 b=g[bid];q=intersect_z([np.array(px)*2400/2048],f'frame_{sec:06.2f}.jpg',b['roof_edge_height']+h+.45)[0,:2];xy=np.array(b['footprint_world']);edge=xy[1]-xy[0];yaw=np.arctan2(edge[1],edge[0]);R=np.array([[np.cos(yaw),-np.sin(yaw)],[np.sin(yaw),np.cos(yaw)]]);v=(xy-xy.mean(0))@R;q=(q-xy.mean(0))@R;norm=(q-v.min(0))/np.maximum(.01,np.ptp(v,axis=0));p[bid].setdefault('equipment',[]).append(dict(type=typ,xy=np.clip(norm,.04,.96).tolist(),height=h,radius=rad,stand=.45,provenance='manual source fixture position',source_image=f'frame_{sec:06.2f}.jpg',source_pixel=(np.array(px)*2400/2048).tolist()))
for bid,px in [('V0480',[751,484]),('V0481',[885,547]),('V0483',[1086,660]),('V0484',[1239,732]),('V0485',[1615,887]),('V0485',[1637,891])]:fixture(bid,90,px)
fixture('V0485',90,[1556,859],'heater');fixture('V0504',120,[590,405]);fixture('V0505',120,[539,400])
for bid in ['V0329','V0347','V0354','V0502','V0503','V0513']:
 p[bid]['roof_pattern']='source-visible irregular pale paving repairs'
gdoc['entries']=list(g.values());pdoc['entries']=list(p.values());gpath.write_text(json.dumps(gdoc,ensure_ascii=False));ppath.write_text(json.dumps(pdoc,ensure_ascii=False,indent=2));(P/'manual_village_profile_audit.json').write_text(json.dumps(audit,indent=2));print('MANUAL_FACES',len(audit),'SOURCE_FIXTURES',len(fixtures)-len(excluded),'TOTAL_BODIES',len(g),flush=True)
