from pathlib import Path
p=Path('work/build_architecture_v2.py').read_text().replace('work/buildings/v2','work/buildings/v3').replace('outputs/rectangular-photo-refinement','outputs/orthogonal-multiview').replace('Village_Rectangular_Candidates.blend','Village_Multiview_Refined.blend').replace('V2','V3').replace('rectangular source-refined buildings','orthogonal multiview buildings')
p=p.replace('import bpy,math,json,os,hashlib','import bpy,math,json,os,hashlib,copy\nfrom mathutils.geometry import tessellate_polygon')
p=p.replace("self.groups={};self.curves={}","self.poly=np.array(b.get('plan_polygon',[[0,0],[1,0],[1,1],[0,1]]),float)*[self.W,self.D];self.groups={};self.curves={}")
pos=p.index(' def box(self,')
p=p[:pos]+''' def inside(self,x,y):
  inside=False
  for a,b in zip(self.poly,np.roll(self.poly,-1,axis=0)):
   if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
  return inside
 def slab(self,name,z,thickness,mat):
  edges=np.roll(self.poly,-1,axis=0)-self.poly;normals=np.column_stack([edges[:,1],-edges[:,0]])/np.linalg.norm(edges,axis=1)[:,None];outline=self.poly-.01*(normals+np.roll(normals,1,axis=0));pts=[Vector((x,y,0)) for x,y in outline];n=len(pts);v=[(x,y,z+dz) for dz in [-thickness/2,thickness/2] for x,y in outline];tri=tessellate_polygon([pts]);faces=[]
  for t in tri:
   ids=[(int(q) if isinstance(q,int) else min(range(n),key=lambda i:(pts[i]-q).length)) for q in t];faces.extend([tuple(reversed(ids)),tuple(i+n for i in ids)])
  faces.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
  self.mesh(name,v,faces,mat)
 def clipped_box(self,name,center,dims,mat):
  cx,cy,cz=center;ww,dd,hh=dims;x0,x1=cx-ww/2,cx+ww/2;y0,y1=cy-dd/2,cy+dd/2
  xs=sorted(set([x0,x1]+[float(x) for x,y in self.poly if x0<x<x1]));ys=sorted(set([y0,y1]+[float(y) for x,y in self.poly if y0<y<y1]))
  for a,b in zip(xs,xs[1:]):
   for c,d in zip(ys,ys[1:]):
    if self.inside((a+b)/2,(c+d)/2):self.box(name+' clipped',((a+b)/2,(c+d)/2,cz),(b-a,d-c,hh),mat)
''' +p[pos:]
p=p.replace("  h=np.array(dims)/2;", "  if len(self.poly)>4 and basis is None and name in ('Distinct source roof finish zone','Source dark waterproof repair patch','Source-inspired roof repair paver'):\n   self.clipped_box(name,center,dims,mat);return\n  h=np.array(dims)/2;")
p=p.replace("  key=(mat.name,smooth);", "  if len(self.poly)>4 and name=='Individual source hexagonal terrace paver' and not all(self.inside(v[0],v[1]) for v in verts):return\n  key=(mat.name,smooth);")
p=p.replace("  key=(mat.name,round(r,5));", "  if len(self.poly)>4 and name in ('Roof slab expansion joint','Roof slab transverse joint'):\n   a,z=np.array(points[0]),np.array(points[-1]);ts=sorted(set([0.,1.]+[float((v[k]-a[k])/(z[k]-a[k])) for v in self.poly for k in [0,1] if abs(z[k]-a[k])>1e-8 and 0<(v[k]-a[k])/(z[k]-a[k])<1]))\n   for t0,t1 in zip(ts,ts[1:]):\n    mid=a+(z-a)*(t0+t1)/2\n    if self.inside(*mid[:2]):self.line(name+' clipped',[a+(z-a)*t0,a+(z-a)*t1],r,mat)\n   return\n  key=(mat.name,round(r,5));")
p=p.replace("self.col['rectangular_core']=True", "self.col['rectangular_core']=len(self.poly)==4;self.col['orthogonal_plan']=True;self.col['local_plan_polygon']=json.dumps(self.poly.tolist())")
p=p.replace("Source-refined rectangle; visual review pending", "Orthogonal multiview refinement; hidden details estimated")
p=p.replace(" B.box('Ground floor closed slab',(W/2,D/2,.08),(W,D,.16),MORTAR)"," B.slab('Ground floor orthogonal slab',.08,.16,MORTAR)")
p=p.replace("B.box('Structural floor slab',(W/2,D/2,floor*sh-.10),(W,D,.2),roofmat)","B.slab('Structural floor slab',floor*sh-.10,.2,roofmat)")
p=p.replace(" corners=np.array([[0,0,0],[W,0,0],[W,D,0],[0,D,0]],float)", " corners=np.column_stack([B.poly,np.zeros(len(B.poly))])")
p=p.replace(" for j,(a,z) in enumerate(zip(corners,np.roll(corners,-1,axis=0))):", " for segment,(a,z) in enumerate(zip(corners,np.roll(corners,-1,axis=0))):\n  delta=z-a;j=(0 if delta[0]>0 else 2) if abs(delta[0])>1e-6 else (1 if delta[1]>0 else 3)")
p=p.replace("f=p['facades'][j];wm=wallmats[j]", "f=copy.deepcopy(p['facades'][j]);wm=wallmats[j]\n  fullL=[W,D,W,D][j];u0=[a[0],a[1],W-a[0],D-a[1]][j]\n  f['windows']=[dict(w,x=(w['x']*fullL-u0)/L) for w in f['windows'] if u0+.15<w['x']*fullL<u0+L-.15]\n  f['loggias']=[dict(log,x0=max(0,(log['x0']*fullL-u0)/L),x1=min(1,(log['x1']*fullL-u0)/L)) for log in f.get('loggias',[]) if log['x1']*fullL>u0 and log['x0']*fullL<u0+L]")
p=p.replace("if j==0 and L>2.1", "if j==0 and abs(a[1])<1e-6 and L>2.1")
p=p.replace("if b['type']=='construction' or kind", "if b['type']=='construction' or p.get('unfinished') or kind")
p=p.replace("if b['type'] in ('flat','solar','metal','hip'):","if b['type'] in ('flat','solar','metal','hip') and not p.get('unfinished'):")
p=p.replace("  if b['type'] in ('flat','solar'):","  if b['type'] in ('flat','solar') and not p.get('unfinished'):")
p=p.replace("and L>5 and j==0:","and not p.get('unfinished') and L>5 and j==0:")
p=p.replace("acs=[x for x in p.get('ac_windows',[]) if x['edge']==j]", "acs=[dict(x,x=(x['x']*fullL-u0)/L) for x in p.get('ac_windows',[]) if x['edge']==j and u0+.45<x['x']*fullL<u0+L-.45]")
p=p.replace("(.38)","(.38)") # preserve numeric transforms explicitly below
p=p.replace("patch.outputs['Color'],.38", "patch.outputs['Color'],.22").replace("stain['strength']*2.2", "stain['strength']*1.1").replace("linear([.18,.20,.17])", "linear([.42,.44,.40])").replace("*(rgb*.60)","*(rgb*.78)").replace("*(rgb*.90)","*(rgb*.96)").replace("*(rgb*1.05)","*(rgb*1.03)")
p=p.replace("[.68,.82,.94,1.04,1.11]","[.90,.95,1.0,1.035,1.065]").replace("[.84,.96,1.08,1.16]","[.94,.98,1.02,1.055]")
p=p.replace("[.15,.225,.20],.24,.28", "[.29,.36,.33],.31,.16")
p=p.replace("[(0,.28,.14),(.15,.40,.12)]", "[(0,.20,.09),(.10,.27,.07)]").replace("[(-.16,.25,.12),(0,.38,.16),(.16,.47,.12)]", "[(-.09,.17,.07),(0,.24,.09),(.09,.30,.06)]")
p=p.replace("H+.43,L,.53", "H+.31,L,.43").replace("H+.71,L+.08,.085", "H+.55,L+.06,.065")
p=p.replace("L,.12,.04,.12,WHITE", "L,.065,.015,.06,WHITE")
p=p.replace("xx,cz,.09,hh+.12,.015,.11", "xx,cz,.045,hh+.07,.01,.055").replace("ww+.19,.10,.01,.13", "ww+.11,.055,.01,.065").replace("ww+.20,.11,.07,.37", "ww+.12,.065,.045,.27")
# Source-specific trim, including subdued old-house frames.
a=p.index('def make_building');z=p.index('ledger=',a);body=p[a:z].replace('WHITE','trim');body=body.replace("W,D,H=B.W,B.D,B.H;", "W,D,H=B.W,B.D,B.H;trim=material(b['id']+' / restrained facade trim',p['trim_color']);")
body=body.replace(" # Roof finish and equipment.", """ if p.get('terrace_canopy'):
  c=p['terrace_canopy'];x0,x1=c['x0']*W,c['x1']*W;y0,y1=c['y0']*D,c['y1']*D;ch=c['height'];cm=material(b['id']+' / pale blue terrace canopy',c['color'],.65,.18)
  for x in [x0,x1]:
   for y in [y0,y1]:B.box('Canopy steel post',(x,y,H+ch/2),(.075,.075,ch),FRAME)
  B.box('Raised terrace canopy sheet',((x0+x1)/2,(y0+y1)/2,H+ch),(x1-x0+.2,y1-y0+.2,.06),cm)
  for x in np.arange(x0,x1,.22):B.line('Canopy folded seam',[(x,y0-.1,H+ch+.045),(x,y1+.1,H+ch+.045)],.015,cm)
 # Roof finish and equipment.""")
p=p[:a]+body+p[z:]
p=p.replace("floor*sh-.10,.2,roofmat","floor*sh-.10+(.026 if floor==n else 0),.2,roofmat")
p=p.replace("floor*sh,L,.065,.015,.06,trim","floor*sh,L,(.24 if p.get('unfinished') else .065),.015,(.26 if p.get('unfinished') else .06),trim")
p=p.replace('def box(self,name,center,dims,mat,basis=None):','def box(self,name,center,dims,mat,basis=None,open_ends=()):')
p=p.replace('  if basis is not None and np.linalg.det',"  faces=[f for i,f in enumerate(faces) if not (i==4 and 'start' in open_ends) and not (i==5 and 'end' in open_ends)]\n  if basis is not None and np.linalg.det")
p=p.replace('def box(name,x,zz,ww,hh,depth,thickness,mat):B.box(name,at(x,zz,depth),(ww,thickness,hh),mat,basis)', 'def box(name,x,zz,ww,hh,depth,thickness,mat,open_ends=()):B.box(name,at(x,zz,depth),(ww,thickness,hh),mat,basis,open_ends)')
p=p.replace("x1-x0,z1-z0,-.12,.24,wm)","x1-x0,z1-z0,-.12,.24,wm,tuple(v for v,yes in [('start',abs(x0)<1e-6),('end',abs(x1-L)<1e-6)] if yes))")
p=p.replace("H+.31,L,.43","H+.23,L,.46").replace("H+.55,L+.06,.065","H+.50,L+.06,.065")
p=p.replace("for floor in range(1,n):","for floor in (range(1,n) if p.get('concrete_frame') or p.get('storey_bands') else []):")
p=p.replace("(W-.40,.42,H+.04)","(W-.40,D-.42,H+.04)").replace("np.linspace(.34,.50,5)","np.linspace(D-.50,D-.34,5)")
p=p.replace("s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.1", "s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.25")
p=p.replace("Every residential core constrained to a rectangle; source-aware facade, balcony, roof equipment and weathering profiles. Hidden details remain inferred.", "Orthogonal wall plans permit right-angle recesses; 17 return-reviewed units have explicit corrections. Material revision applied across 297 units. Hidden details and metric dimensions remain estimated.")
p=p.replace("s['V3_scope']=","s.pop('V2_scope',None)\ns['V3_reference_use']='44 and 256 second comparisons, with contextual return frames 252-264 seconds; dimensions remain estimated.'\ns['V3_scope']=")
p=p.replace("and L>2.1 and not b.get('public_hall')","and L>2.1 and not p.get('no_inferred_door') and not b.get('public_hall')")
Path('work/build_architecture_v3.py').write_text(p)
compile(p,'v3','exec');print('V3_BUILDER_WRITTEN')
