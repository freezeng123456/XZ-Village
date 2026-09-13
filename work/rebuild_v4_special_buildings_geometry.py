"""Geometric public structures measured against native source views."""
def traditional_roof(B,b,p,H,rm):
 xy=B.xy;mn=xy.min(0)-.24;mx=xy.max(0)+.24;size=mx-mn;axis=int(size.argmax());short=1-axis;mid=(mn[short]+mx[short])/2;rh=b['ridge_height']-b['roof_edge_height'];roof=b['roof_edge_height']-B.base;nx=max(12,int(size[axis]/.23));ny=max(8,int(size[short]/.7));rng=np.random.default_rng(sum(map(ord,b['id'])));materials=[]
 for k in range(5):materials.append(finish_material(B.id+f' aged clay {k}',np.clip(np.array(p['roof_color'])*(.81+k*.085),0,1),'plaster',.55,2))
 def point(x,t,side,extra=0):
  q=np.zeros(3);q[axis]=x;q[short]=mid+side*t*size[short]/2;end=abs((x-(mn[axis]+mx[axis])/2)/(size[axis]/2));q[2]=roof+rh*max(0,1-t)**1.38+.20*t**7+.42*end**10+.035+extra;return q
 for side in [-1,1]:
  for ix in range(nx):
   x0=mn[axis]+size[axis]*ix/nx;x1=mn[axis]+size[axis]*(ix+1)/nx
   for iy in range(ny):
    t0=iy/ny;t1=min(1.015,(iy+1.06)/ny);v=[point(x0,t0,side),point(x1,t0,side),point(x1,t1,side),point(x0,t1,side)];B.mesh('Source hall overlapping curved clay tile',v,[(0,1,2,3)],materials[int(rng.integers(5))]);B.line('Tile barrel crest',[point((x0+x1)/2,t0,side,.025),point((x0+x1)/2,t1,side,.025)],.023,materials[(ix+iy)%5])
  for x in [mn[axis],mx[axis]]:
   pts=[point(x,t,side,.065) for t in np.linspace(0,1,24)];B.line('Raised curved gable verge',pts,.13,CONCRETE)
  B.line('Upturned hall eave moulding',[point(x,1,side,.01) for x in np.linspace(mn[axis],mx[axis],48)],.12,CONCRETE)
 # Close the curved roof at both masonry gable ends.
 wall=finish_material(B.id+' traditional gable masonry',p['color'],p['style'],p.get('wall_age',.5),0)
 for x in [mn[axis]+.13,mx[axis]-.13]:
  v=[point(x,t,-1) for t in np.linspace(1,0,20)]+[point(x,t,1) for t in np.linspace(0,1,20)];a=v[-1].copy();a[2]=H-.04;c=v[0].copy();c[2]=H-.04;v.extend([a,c]);B.mesh('Masonry traditional curved gable wall',v,[tuple(range(len(v)))],wall)
 B.line('Raised curved traditional ridge',[point(x,0,1,.15) for x in np.linspace(mn[axis],mx[axis],64)],.17,CONCRETE)
 # Ridge ends sweep upwards, a visible identifying feature of this hall.
 for sgn in [-1,1]:
  end=mn[axis] if sgn<0 else mx[axis];a=point(end,0,1,.15);v=[]
  for t in np.linspace(0,1,10):q=a.copy();q[axis]+=sgn*t*.50;q[2]+=.55*t*t;v.append(q)
  B.line('Upturned ridge end ornament',v,.11,CONCRETE)

def special_structure(b,p):
 kind=b.get('special_model');B=Geometry(b);xy=B.xy;mn=xy.min(0);mx=xy.max(0);H=b['roof_edge_height']-B.base;roofmat=finish_material(B.id+' special roof',p['roof_color'],'plaster',.22,2);wallmat=finish_material(B.id+' special masonry',p['color'],'plaster',.34,0)
 if kind=='six_column_pavilion':
  center=xy.mean(0);rad=float(np.linalg.norm(xy-center,axis=1).mean());B.slab('Hexagonal pavilion platform',.20,.40,CONCRETE);inner=center+(xy-center)*.77
  for q in inner:
   B.cylinder('Pavilion hexagon support column',(*q,H/2),.16,H,TRIM,12);B.cylinder('Pavilion column base',(*q,.24),.24,.25,CONCRETE,12);B.cylinder('Pavilion column capital',(*q,H-.12),.25,.24,TRIM,12)
  for k,(a,c) in enumerate(zip(inner,np.roll(inner,-1,axis=0))):
   B.line('Pavilion lintel',[[*a,H-.10],[*c,H-.10]],.12,TRIM)
   if k==3:continue
   for z in [.65,1.13]:B.line('Pavilion balustrade rail',[[*a,z],[*c,z]],.07,TRIM)
   for t in np.arange(.20,.95,.23):q=a+(c-a)*t;B.cylinder('Pavilion balustrade spindle',(*q,.87),.035,.52,TRIM,8)
  # Radial curved tiles follow all six roof sectors and upturned corners.
  nr=15;nt=12;rise=b['ridge_height']-b['roof_edge_height'];rings=[]
  for k in range(6):
   a=xy[k]-center;c=xy[(k+1)%6]-center
   for j in range(nt):
    t0=j/nt;t1=(j+1)/nt
    for ir in range(nr):
     r0=max(.015,ir/nr);r1=(ir+1.025)/nr;v=[]
     for r,t in [(r0,t0),(r0,t1),(r1,t1),(r1,t0)]:q=center+((1-t)*a+t*c)*r;z=H+rise*max(0,1-r)**1.8+.20*r**7+.23*r**7*(abs(t-.5)*2)**4;v.append([*q,z])
     B.mesh('Hexagonal curved pavilion roof tile',v,[(0,1,2,3)],roofmat)
   pts=[]
   for r in np.linspace(.015,1,28):q=center+a*r;pts.append([*q,H+rise*max(0,1-r)**1.8+.43*r**7+.045])
   B.line('Pavilion hip ridge',pts,.055,roofmat);B.line('Pavilion white eave fascia',[[*(center+(1-t)*a+t*c),H+.20+.23*(abs(t-.5)*2)**4] for t in np.linspace(0,1,18)],.12,TRIM)
  B.cylinder('Pavilion finial base',(*center,H+rise+.13),.12,.28,TRIM,16);B.cylinder('Pavilion finial point',(*center,H+rise+.34),.07,.18,TRIM,12);return B.done()
 if kind=='open_stage':
  front=b['front_face'];a=np.r_[xy[front],0];u=np.r_[xy[(front+1)%len(xy)]-xy[front],0];L=np.linalg.norm(u);u/=L;sgn=1 if np.sum(xy[:,0]*np.roll(xy[:,1],-1)-np.roll(xy[:,0],-1)*xy[:,1])>0 else -1;out=np.array([u[1],-u[0],0])*sgn;basis=np.array([u,out,[0,0,1]]);depth=float(np.ptp(xy@out[:2]));blue=material('Stage blue trim',[.13,.26,.36]);stagefloor=material('Stage worn floor',[.44,.45,.41]);curtain=material('Stage interior dark curtain',[.12,.15,.14]);red=material('Stage front fascia',[.49,.13,.13])
  def at(x,z,dep=0):return a+u*x+out*dep+[0,0,z]
  def box(name,x,z,w,h,dep,th,mat):B.box(name,at(x,z,dep),(w,th,h),mat,basis)
  B.slab('Raised stage full platform',.52,1.04,stagefloor);B.slab('Stage roof ceiling',H-.12,.12,wallmat)
  for j,(aa,cc) in enumerate(zip(xy,np.roll(xy,-1,axis=0))):
   if j==front:continue
   edge=cc-aa;leng=np.linalg.norm(edge);bb=np.array([[*(edge/leng),0],[-edge[1]/leng,edge[0]/leng,0],[0,0,1]]);B.box('Enclosed stage rear or side wall',(*(aa+cc)/2,H/2),(leng,.22,H),wallmat,bb)
  l=L*.175;r=L*.825;openingheight=H*.66;bottom=1.04;top=bottom+openingheight
  for x,w in [(l/2,l),((r+L)/2,L-r)]:
   box('Stage flank lower wall',x,1.63,w,1.18,0,.24,wallmat);box('Stage flank upper wall',x,(3.1+H)/2,w,H-3.1,0,.24,red);box('Stage flank window recess',x,2.65,w*.72,.86,-.06,.12,DARK);box('Stage flank window',x,2.65,w*.66,.78,-.10,.025,FRAME)
   for xx in [x-w*.36,x,x+w*.36]:box('Stage flank window frame',xx,2.65,.065,.86,.015,.065,TRIM)
  box('Stage opening top wall',(l+r)/2,(top+H)/2,r-l,H-top,0,.25,red)
  for x in [l,r]:box('Stage opening blue jamb',x,(bottom+top)/2,.23,top-bottom,.12,.20,blue)
  box('Stage opening top beam',(l+r)/2,top,r-l+.23,.18,.12,.20,blue);box('Source red sign fascia without unreadable lettering',(l+r)/2,top-.37,r-l-.35,.60,-.06,.15,red)
  box('Recessed performance backdrop',L/2,(bottom+top)/2,r-l,top-bottom,-depth*.70,.10,curtain);box('Performance floor inset',L/2,1.06,r-l,.05,-depth*.40,depth*.8,curtain)
  for k in range(6):box('Front entrance stair',L*.44,.085*(k+1),L*.29,.17*(k+1),1.8-k*.25,.29,wallmat)
  # Hipped sheet roof, with its wide front slope and lower side eaves.
  x0,y0=mn-.43;x1,y1=mx+.43;cx=(x0+x1)/2;cy=(y0+y1)/2;W=x1-x0;D=y1-y0;rise=b['ridge_height']-b['roof_edge_height'];v=[[x0,y0,H],[x1,y0,H],[x1,y1,H],[x0,y1,H],[x0+W*.10,cy,H+rise],[x1-W*.10,cy,H+rise]];fs=[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)];B.mesh('Source stage hipped red sheet roof',v,fs,roofmat)
  for face in fs:
   for aa,cc in zip(face,face[1:]+face[:1]):B.line('Stage roof edge flashing',[v[aa],v[cc]],.055,roofmat)
  for k in np.arange(0,1,.025):
   for a1,a2,b1,b2 in [(0,1,4,5),(3,2,4,5)]:B.line('Stage corrugation seam',[np.array(v[a1])*(1-k)+np.array(v[a2])*k,np.array(v[b1])*(1-k)+np.array(v[b2])*k],.012,roofmat)
  B.openings=3;return B.done()
 return None
