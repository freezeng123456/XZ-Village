"""Blender geometry for source-located ground surfaces and canopy observations."""
def add_environment(env):
 B=Geometry(dict(id='SITE',name='Source-located village environment',footprint_world=[[-1,-1],[1,-1],[1,1],[-1,1]],base_height=0));mats={}
 for kind,c,age in [('bank',[.43,.43,.36],.65),('road',[.63,.62,.57],.32),('plowed',[.47,.42,.33],.52),('mulch',[.64,.65,.60],.30),('crops',[.32,.43,.20],.28)]:mats[kind]=finish_material('Site '+kind,c,'plaster',age,2)
 water=material('Pond water',[.24,.32,.29],.19,.28);nt=water.node_tree;bs=nt.nodes.get('Principled BSDF');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=16;noise.inputs['Detail'].default_value=3;bn=nt.nodes.new('ShaderNodeBump');bn.inputs['Strength'].default_value=.13;bn.inputs['Distance'].default_value=.028;nt.links.new(noise.outputs['Fac'],bn.inputs['Height']);nt.links.new(bn.outputs[0],bs.inputs['Normal']);mats['water']=water
 for e in env['surfaces']:
  if e['vertices']:B.mesh(e['name'],e['vertices'],e['faces'],mats[e['kind']])
 for e in env['field_rows']:B.line('Source-oriented agricultural row',e['points'],e['width'],mats[e['kind']])
 # Pond edge stones are geometric, with source-located outlines.
 shore=finish_material('Pond masonry edge',[.48,.48,.42],'brick',.65,0)
 for pond in env.get('water_outlines',[]):
  xy=np.array(pond['xy']);z=pond['z']
  for a,c in zip(xy,xy[1:]):
   length=np.linalg.norm(c-a);num=max(1,int(length/.95));edge=(c-a)/max(length,.01);basis=np.array([[*edge,0],[-edge[1],edge[0],0],[0,0,1]])
   for j in range(num):q=a+(c-a)*(j+.5)/num;B.box('Pond edge masonry block',(*q,z+.22),(length/num-.025,.28,.45),shore,basis)
 # Foliage geometry is synthesized around observed crown cells; no image planes.
 foliage=[]
 for k in range(7):
  c=np.array([.29,.38,.18])*([.78,.88,.95,1.02,1.09,1.18,1.28][k]);m=finish_material(f'Foliage variation {k}',np.clip(c,0,1),'plaster',.10,2);nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');bn=nt.nodes.get('Bump');
  if bn:bn.inputs['Strength'].default_value=.42;bn.inputs['Distance'].default_value=.055
  bs.inputs['Roughness'].default_value=.85;foliage.append(m)
 bark=finish_material('Tree bark',[.32,.285,.22],'plaster',.45,0)
 # An icosahedron subdivided once provides an economical irregular crown lobe.
 golden=(1+math.sqrt(5))/2;unit=np.array([[-1,golden,0],[1,golden,0],[-1,-golden,0],[1,-golden,0],[0,-1,golden],[0,1,golden],[0,-1,-golden],[0,1,-golden],[golden,0,-1],[golden,0,1],[-golden,0,-1],[-golden,0,1]],float);unit/=np.linalg.norm(unit,axis=1)[:,None];faces=[(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),(1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),(3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),(4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)];verts=unit.tolist();cache={};newfaces=[]
 def midpoint(a,b):
  key=tuple(sorted([a,b]))
  if key not in cache:
   v=np.array(verts[a])+verts[b];v/=np.linalg.norm(v);cache[key]=len(verts);verts.append(v.tolist())
  return cache[key]
 for a,b,c in faces:
  ab=midpoint(a,b);bc=midpoint(b,c);ca=midpoint(c,a);newfaces.extend([(a,ab,ca),(b,bc,ab),(c,ca,bc),(ab,bc,ca)])
 unit=np.array(verts);rng=np.random.default_rng(81129)
 for i,t in enumerate(env['trees']):
  center=np.array(t['xy']);height=t['height'];base=t['base'];rad=t['radius'];trunkh=height*.70;B.cylinder('Observed canopy supporting trunk',(*center,base+trunkh/2),min(.26,rad*.065),trunkh,bark,8)
  n=7 if height>5 else 5
  for j in range(n):
   angle=j*math.tau/n+rng.uniform(-.3,.3);off=np.array([math.cos(angle),math.sin(angle)])*rad*(.48 if j else 0);cc=np.r_[center+off,base+height*.71+rng.uniform(-.12,.12)*height];scale=np.array([rad*.72,rad*.72,min(height*.33,rad*.86)])*rng.uniform(.80,1.15,3);v=unit*scale*(rng.uniform(.89,1.11,len(unit))[:,None])+cc;B.mesh('Inferred crown lobe around observed vegetation',v,newfaces,foliage[int(rng.integers(len(foliage)))]);
   if j%2==0:B.line('Tree crown branch',[(*center,base+height*.40),(*cc[:2],cc[2]-.30)],.047,bark)
 report=B.done()
 for ob in B.col.objects:
  if ob.type=='MESH' and ob.data.materials and ob.data.materials[0].name.startswith('Foliage'):
   for face in ob.data.polygons:face.use_smooth=True
 return report
