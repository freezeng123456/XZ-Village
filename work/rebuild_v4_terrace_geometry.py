"""Observed stepped top floor: lower terrace, full-height return walls and open corner."""
def add_top_terrace(B,b,p,H,wm):
 spec=b.get('top_floor_terrace')
 if not spec:return
 q=(np.array(spec['notch_world'])-B.origin)@B.R;floor=spec['floor'];level=floor*H/b['floor_count'];height=H-level
 for a,c in [(q[1],q[2]),(q[2],q[3])]:
  ed=c-a;length=np.linalg.norm(ed);basis=np.array([[*(ed/length),0],[-ed[1]/length,ed[0]/length,0],[0,0,1]]);B.box('Source upper terrace full-height return wall',(*(a+c)/2,level+height/2),(length,.22,height),wm,basis)
 for a,c in [(q[0],q[1]),(q[3],q[0])]:
  ed=c-a;length=np.linalg.norm(ed);basis=np.array([[*(ed/length),0],[-ed[1]/length,ed[0]/length,0],[0,0,1]]);B.box('Source open terrace masonry parapet',(*(a+c)/2,level+.45),(length,.16,.90),wm,basis);B.line('Upper terrace parapet coping',[(*a,level+.92),(*c,level+.92)],.09,TRIM)
