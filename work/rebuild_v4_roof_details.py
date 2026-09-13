"""Roof geometry helpers used inside Blender; independent editable mesh parts."""
def inside_polygon(point,poly):
 x,y=point;yes=False
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes

def roof_plane(B,b):
 coeff=np.array(b.get('observed_surface_plane',[0,0,b['roof_edge_height']]),float)
 if np.linalg.norm(coeff[:2])>.7:coeff=np.array([0,0,b['roof_edge_height']])
 def z(xy):
  q=np.asarray(xy)@B.R.T+B.origin;return q[...,0]*coeff[0]+q[...,1]*coeff[1]+coeff[2]-B.base
 center=float(z(B.xy.mean(0)));lo=b['roof_edge_height']-B.base
 if not(lo-.3<center<lo+4):
  shift=lo-center
  def corrected(xy):return z(xy)+shift
  return corrected
 return z

def sheet_roof(B,b,p,H,rm):
 xy=B.xy;plane=roof_plane(B,b);poly=np.column_stack([xy,plane(xy)]);B.mesh('Measured sloping sheet roof',poly,[tuple(range(len(xy)))],rm);mn=xy.min(0);mx=xy.max(0);is_solar=b['roof_type']=='solar'
 if not is_solar and b.get('source_role')!='canopy':
  wall=finish_material(B.id+' sloping eave infill',p['color'],p['style'],p.get('wall_age',.3),0)
  for a,c in zip(xy,np.roll(xy,-1,axis=0)):
   za=float(plane(a));zc=float(plane(c))
   if max(za,zc)>H+.015:B.mesh('Wall infill up to measured sloping eave',[[*a,H-.03],[*c,H-.03],[*c,max(H,zc)],[*a,max(H,za)]],[(0,1,2,3)],wall)

 for a,c in zip(poly,np.roll(poly,-1,axis=0)):B.line('Roof sheet edge flashing',[a,c],.045,STEEL if is_solar else rm)
 if is_solar:
  for a,c in zip(xy,np.roll(xy,-1,axis=0)):
   length=np.linalg.norm(c-a)
   for t in np.linspace(.03,.97,max(2,int(length/3.8)+1)):
    q=a+(c-a)*t;top=float(plane(q))-.02
    if top>H:B.box('Solar canopy support post',(*q,(top+H)/2),(.065,.065,top-H),STEEL)
  sx,sy=1.06,1.80
  for x in np.arange(mn[0]+.025,mx[0]-.2,sx):
   for y in np.arange(mn[1]+.025,mx[1]-.2,sy):
    x1=min(x+sx-.045,mx[0]-.015);y1=min(y+sy-.045,mx[1]-.015)
    if not all(inside_polygon(q,xy) for q in [(x+.02,y+.02),(x1-.02,y+.02),(x1-.02,y1-.02),(x+.02,y1-.02)]):continue
    qq=np.array([[x,y],[x1,y],[x1,y1],[x,y1]]);vv=np.column_stack([qq,plane(qq)+.04]);B.mesh('Photovoltaic module',vv,[(0,1,2,3)],SOLAR)
    for a,c in zip(vv,np.roll(vv,-1,axis=0)):B.line('PV module aluminum frame',[a,c],.018,STEEL)
    for xx in np.linspace(x,x1,7)[1:-1]:
     qq=np.array([[xx,y],[xx,y1]]);B.line('PV cell vertical grid',np.column_stack([qq,plane(qq)+.045]),.0038,STEEL)
    for yy in np.linspace(y,y1,13)[1:-1]:
     qq=np.array([[x,yy],[x1,yy]]);B.line('PV cell horizontal grid',np.column_stack([qq,plane(qq)+.045]),.0038,STEEL)
 else:
  # Folded corrugations follow the source roof's own axes.
  for x in np.arange(mn[0],mx[0],.21):
   segments=[]
   for y in np.arange(mn[1],mx[1]+.05,.22):
    if inside_polygon([x,y],xy):segments.append((x,y,float(plane([x,y]))+.026))
    elif len(segments)>1:B.line('Corrugated roof raised seam',segments,.018,rm);segments=[]
   if len(segments)>1:B.line('Corrugated roof raised seam',segments,.018,rm)

def roof_rectangles(xy):
 # Decompose actual orthogonal concavities into adjoining roof wings.
 xs=np.unique(np.round(xy[:,0],3));ys=np.unique(np.round(xy[:,1],3));cells=[]
 for y0,y1 in zip(ys,ys[1:]):
  row=[]
  for x0,x1 in zip(xs,xs[1:]):
   if inside_polygon([(x0+x1)/2,(y0+y1)/2],xy):
    if row and abs(row[-1][2]-x0)<.02:row[-1][2]=x1
    else:row.append([x0,y0,x1,y1])
  cells.extend(row)
 merged=[]
 for rect in cells:
  for old in merged:
   if abs(old[0]-rect[0])<.02 and abs(old[2]-rect[2])<.02 and abs(old[3]-rect[1])<.02:old[3]=rect[3];break
  else:merged.append(rect)
 return merged

def tile_pitch(B,origin,along,down,width,depth,rm,seed):
 origin=np.array(origin);along=np.array(along);down=np.array(down);normal=np.cross(along,down);normal/=np.linalg.norm(normal)
 if normal[2]<0:normal=-normal
 nx=max(1,int(width/.23));ny=max(1,int(depth/.40));w=width/nx;h=depth/ny;colors=[];rng=np.random.default_rng(seed)
 base=np.array(rm.diffuse_color[:3])
 for k in range(5):
  # Base shader is reused; linked material copies vary clay firing and weathering.
  mm=rm.copy();mm.name=rm.name+f' tile variation {seed}_{k}';bs=mm.node_tree.nodes.get('Principled BSDF');mm.diffuse_color=(*np.clip(base*(.82+k*.075),0,1),1)
  for node in mm.node_tree.nodes:
   if node.type=='VALTORGB' and node.color_ramp.elements[0].color[0]>.01:
    for el in node.color_ramp.elements:el.color=(*np.clip(np.array(el.color[:3])*(.82+k*.075),0,1),1)
  colors.append(mm)
 for ix in range(nx):
  for iy in range(ny):
   x=ix*w;y=iy*h;vs=[]
   for ddy,raisez in [(0,.026),(h*1.045,.01)]:
    for fraction,bend in [(0,0),(.28,.017),(.72,.017),(1,0)]:vs.append(origin+along*(x+w*fraction)+down*(y+ddy)+normal*(raisez+bend))
   B.mesh('Individual overlapping clay tile',vs,[(0,4,5,1),(1,5,6,2),(2,6,7,3)],colors[int(rng.integers(0,5))])

def pitched_roof(B,b,p,H,rm):
 xy=B.xy;roof=b['roof_edge_height']-B.base;totalridge=max(.55,min(4.5,b.get('ridge_height',b['roof_edge_height']+1.25)-b['roof_edge_height']));rects=roof_rectangles(xy)
 if not rects:rects=[[*xy.min(0),*xy.max(0)]]
 for k,r in enumerate(rects):
  mn=np.array(r[:2]);mx=np.array(r[2:]);size=mx-mn
  if min(size)<.3:continue
  ax=int(size.argmax());short=1-ax;ridge=min(totalridge,size[short]*.43);v=[]
  for end in [mn[ax]-.13,mx[ax]+.13]:
   for side,z in [(mn[short]-.13,roof),(float((mn[short]+mx[short])/2),roof+ridge),(mx[short]+.13,roof)]:
    q=[0,0,z];q[ax]=end;q[short]=side;v.append(q)
  B.mesh('Source-aligned pitched roof wing',v,[(0,3,4,1),(1,4,5,2)],rm);B.mesh('Masonry gable ends',v,[(0,1,2),(5,4,3)],CONCRETE);B.line('Raised ridge cap',[v[1],v[4]],.09,rm)
  for aa,bb,cc in [(v[1],v[4],v[0]),(v[1],v[4],v[2])]:
   along=np.array(bb)-aa;down=np.array(cc)-aa;width=np.linalg.norm(along);depth=np.linalg.norm(down)
   if b['roof_type']=='gable':tile_pitch(B,aa,along/width,down/depth,width,depth,rm,(sum(map(ord,b['id']))*17+k)%10000)
   else:
    for t in np.arange(0,width,.20):B.line('Metal pitch corrugation',[np.array(aa)+along*t/width,np.array(aa)+along*t/width+down],.015,rm)
