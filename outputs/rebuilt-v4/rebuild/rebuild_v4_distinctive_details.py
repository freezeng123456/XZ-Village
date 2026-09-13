"""Source-specific arches, curved stair glazing, bay windows and trims in Blender."""
def curved_stair_bay(B,a,u,out,L,H,wm,glass,spec):
 sag=spec.get('sag',.72);R=(L*L/4+sag*sag)/(2*sag);limit=math.asin(min(.99,L/(2*R)));ts=np.linspace(-limit,limit,31);cx=L/2
 def point(t,z,offset=0):return a+u*(cx+R*math.sin(t))+out*(R*math.cos(t)-(R-sag)+offset)+[0,0,z]
 tx0=math.asin((spec['window_x0']*L-cx)/R);tx1=math.asin((spec['window_x1']*L-cx)/R);ts=sorted(set(ts.tolist()+[tx0,tx1]));bt=spec['window_bottom']*H;top=spec['window_top']*H;zs=[0,bt,top,H]
 for t0,t1 in zip(ts,ts[1:]):
  for z0,z1 in zip(zs,zs[1:]):
   mat=glass if tx0<(t0+t1)/2<tx1 and bt<(z0+z1)/2<top else wm;vv=[point(t0,z0),point(t1,z0),point(t1,z1),point(t0,z1)];B.mesh('Curved stair bay glazing' if mat==glass else 'Curved ceramic stair bay wall',vv,[(0,1,2,3)],mat)
 for t in np.linspace(tx0,tx1,4):B.line('Continuous stair window vertical mullion',[point(t,bt,.025),point(t,top,.025)],.027,TRIM)
 for z in np.linspace(bt,top,18):B.line('Curved stair glazing transom',[point(t,z,.025) for t in np.linspace(tx0,tx1,14)],.025,TRIM)
 for z in [bt-.06,top+.08,H,H+.15]:B.line('Curved stair bay cornice',[point(t,z,.045) for t in ts],.055,TRIM)
 vv=[point(t,H+.01) for t in ts];vv.append(a+u*L);vv[-1][2]=H+.01;vv.append(a.copy());vv[-1][2]=H+.01;B.mesh('Curved stair bay roof cap',vv,[tuple(range(len(vv)))],TRIM)

def arch_spandrel(B,at,l,r,bt,t,wm):
 rise=min(.70,(r-l)*.18);cx=(l+r)/2;pts=[]
 for x in np.linspace(l,r,21):
  z=t-rise+rise*math.sqrt(max(0,1-((x-cx)/((r-l)/2))**2));pts.append((x,z))
 for (x0,z0),(x1,z1) in zip(pts,pts[1:]):
  B.mesh('Masonry above source arch', [at(x0,z0,-.01),at(x1,z1,-.01),at(x1,t+.02,-.01),at(x0,t+.02,-.01)],[(0,1,2,3)],wm)
 B.line('Arched opening moulding',[at(x,z,.055) for x,z in pts],.072,TRIM)

def facade_modulations(B,f,at,boxat,L,H,n,basis,wm,glass):
 if f.get('floor_bands'):
  ac=material(B.id+' source accent band',f.get('accent_color',[.73,.72,.67]))
  for k in range(1,n+1):
   z=k*H/n
   for dz,ht,depth,mat in [(-.23,.095,.10,ac),(-.09,.08,.14,TRIM),(.035,.06,.16,TRIM)]:boxat('Source horizontal facade band',L/2,z+dz,L+.08,ht,depth,.10,mat)
 for v in f.get('ornamental_pilasters',[]):
  x=v*L;boxat('Source pilaster shaft',x,H/2,.18,H,.12,.16,TRIM)
  for k in range(n):
   for z,w,h in [(k*H/n+.20,.29,.16),((k+1)*H/n-.28,.31,.18),((k+1)*H/n-.11,.38,.12)]:boxat('Pilaster capital and base',x,z,w,h,.15,.20,TRIM)
 for spec in f.get('bay_windows',[]):
  l=spec['x0']*L;r=spec['x1']*L;bt=spec['bottom']*H;top=spec['top']*H;dep=spec['depth'];ch=(r-l)*.16;path=[(l,0),(l+ch,dep),(r-ch,dep),(r,0)]
  for (x0,d0),(x1,d1) in zip(path,path[1:]):
   B.mesh('Chamfered projecting bay glass',[at(x0,bt,d0),at(x1,bt,d1),at(x1,top,d1),at(x0,top,d0)],[(0,1,2,3)],glass)
   for x,dv in [(x0,d0),(x1,d1),((x0+x1)/2,(d0+d1)/2)]:B.line('Bay window vertical frame',[at(x,bt,dv+.02),at(x,top,dv+.02)],.032,TRIM)
   for z in [bt,bt+(top-bt)*.75,top]:B.line('Bay window horizontal frame',[at(x0,z,d0+.02),at(x1,z,d1+.02)],.032,TRIM)
  for z in [bt-.30,bt-.18,top+.12,top+.25]:B.line('Bay window stone cornice',[at(x,z,dv+.10) for x,dv in path],.07,TRIM)
 if f.get('front_awning'):
  sp=f['front_awning'];l=sp['x0']*L;r=sp['x1']*L;z=sp['height']*H;dep=sp['depth'];mat=material(B.id+' source front awning',sp['color']);B.mesh('Source metal entrance awning',[at(l,z,.10),at(r,z,.10),at(r,z-.45,dep),at(l,z-.45,dep)],[(0,1,2,3)],mat)
  for x in np.arange(l,r,.22):B.line('Entrance awning corrugation',[at(x,z+.02,.10),at(x,z-.43,dep)],.018,mat)
 if f.get('roof_balustrade'):
  stone=f['roof_balustrade']=='stone';mat=TRIM if stone else FRAME
  for z in [H+.18,H+1.02]:boxat('Source rooftop railing horizontal',L/2,z,L,.11 if stone else .06,.015,.18 if stone else .06,mat)
  for x in np.arange(.12,L-.03,.25 if stone else .16):
   if stone:
    for z0,z1,r in [(.23,.39,.05),(.39,.54,.032),(.54,.75,.052),(.75,.95,.032)]:B.cylinder('Rooftop turned stone baluster',at(x,H+(z0+z1)/2,.015),r,z1-z0,TRIM,8)
   else:B.line('Rooftop metal baluster',[at(x,H+.20,.015),at(x,H+1.02,.015)],.015,FRAME)
  for x in np.arange(.06,L,2.2):boxat('Rooftop railing masonry post',x,H+.53,.18,1.06,.015,.20,TRIM)
 if f.get('sheet_cladding') or f.get('sheet_cladding_upper'):
  bottom=H/2 if f.get('sheet_cladding_upper') else 0
  for x in np.arange(.04,L,.19):B.line('Source vertical folded sheet wall seam',[at(x,bottom+.02,.015),at(x,H-.03,.015)],.022,wm)
 if f.get('scaffold'):
  scmat=material('Construction scaffold weathered metal',[.53,.53,.47],.60,.38);dep=.58;step=1.35
  for x in np.arange(.02,L+.01,step):B.line('Source scaffold vertical standard',[at(x,.04,dep),at(x,H+.80,dep)],.032,scmat)
  for z in np.arange(.22,H+.80,1.50):
   B.line('Source scaffold horizontal ledger',[at(.02,z,dep),at(L-.02,z,dep)],.03,scmat)
   for x in np.arange(.02,L,step):B.line('Scaffold wall tie',[at(x,z,.06),at(x,z,dep)],.023,scmat)
  for x in np.arange(.02,L-1,step*2):
   for z in np.arange(.22,H-1.0,3.0):B.line('Scaffold diagonal brace',[at(x,z,dep+.025),at(min(L,x+step*2),min(H+.50,z+3.0),dep+.025)],.025,scmat)
  if f.get('construction_screen'):
   scr=material('Source black construction screen',[.10,.11,.10],.9);B.mesh('Observed hanging construction screening',[at(L*.43,.40,dep-.07),at(L*.97,.50,dep-.07),at(L*.94,H+.40,dep-.04),at(L*.48,H+.65,dep-.03)],[(0,1,2,3)],scr)
 if f.get('public_facade'):
  teal=material('Public building turquoise doors and trim',[.25,.56,.55]);pink=material('Public building pink fascia',[.81,.60,.64]);red=material('Public central raised red fascia',[.66,.31,.25]);dep=1.15
  # Long outward corridor slabs, waist-high fascia and source front steps.
  for k in [0,1]:
   z=k*H/2+.025;boxat('Continuous public corridor floor',L/2,z,L,.15,dep/2,dep+.12,TRIM)
   if k:
    boxat('Public corridor solid pink parapet',L/2,z+.60,L,.88,dep,.16,pink);boxat('Public corridor stone coping',L/2,z+1.075,L,.09,dep,.24,TRIM)
  boxat('Public roof wide pink frieze',L/2,H-.06,L,.68,dep,.16,pink)
  for k in range(3):boxat('Full-width public entrance step',L/2,-.12-k*.12,L+.30,.12,dep+.25+k*.28,.31,TRIM)
  for x in [0,L]:boxat('Public corridor end return',x,H/2,.14,H,dep/2,dep,wm)
  for xx in [.305,.38,.625,.70]:
   boxat('Source red corridor upright',L*xx,H*.76,.17,H*.53,dep+.12,.20,red)
   boxat('Source fascia upright cap',L*xx,H+.64,.26,1.2,dep+.16,.23,red)
  boxat('Raised central red sign fascia',L*.503,H+.64,L*.405,1.02,dep+.11,.18,red)
  for z in [H+.12,H+1.16]:boxat('Central raised fascia moulding',L*.503,z,L*.414,.10,dep+.14,.24,red)
  for x in [L*.065,L*.94]:
   z=H+.45;w=L*.051
   vs=[at(x-w,z-.32,dep),at(x-w*.68,z+.48,dep),at(x+w*.68,z+.48,dep),at(x+w,z-.32,dep)];B.mesh('Raised end circular-vent parapet',vs,[(0,1,2,3)],pink)
   B.line('Circular parapet vent rim',[at(x+.29*math.cos(t),z+.08+.29*math.sin(t),dep+.04) for t in np.linspace(0,math.tau,49)],.045,TRIM)
   B.mesh('Dark round parapet vent',[at(x,z+.08,dep+.025)]+[at(x+.25*math.cos(t),z+.08+.25*math.sin(t),dep+.025) for t in np.linspace(0,math.tau,49)],[(0,j,j+1) for j in range(1,49)],DARK)
  # Visible central stair flights extend into the measured open stairwell.
  sx=L*.515;sw=L*.032;steps=16;rise=H/2/steps
  for level in [0,1]:
   for k in range(steps):boxat('Visible central concrete stair tread',sx,level*H/2+k*rise+.09,sw,.18,-k*.21,.25,TRIM)
   boxat('Central stair landing',sx+sw*.30,(level+1)*H/2-.10,sw*1.7,.16,-3.3,.9,CONCRETE)
  for x in [sx-sw*.53,sx+sw*.53]:B.line('Central staircase handrail',[at(x,.8,.03),at(x,H/2+.8,-3.2)],.035,TRIM)
