"""Place visible roof cylinders/vents from annotated pixels, not roof centres."""
import json,numpy as np,cv2
from pathlib import Path
root=Path('work/buildings');data=json.loads((root/'architecture_candidates.json').read_text());bs={b['id']:b for b in data['buildings']};poses=json.loads((root/'visibility/poses.json').read_text())
rows=[('B002',44,632,533,'vent'),('B003',44,559,592,'tank'),('B005',44,397,523,'tank'),('B006',44,320,434,'tank'),('B008',44,132,420,'tank'),('B012',44,552,395,'tank'),('B023',44,308,278,'tank'),('B028',44,345,584,'tank'),('B029',44,402,799,'tank'),('B030',44,772,653,'tank'),('B030',44,796,658,'tank'),('B031',44,769,730,'tank'),('B034',44,514,710,'tank'),('B035',44,348,267,'tank'),('A007',0,465,751,'tank'),('A008',0,491,540,'tank'),('A014',0,347,564,'tank'),('A016',0,142,608,'tank'),('A018',0,217,502,'tank'),('A020',0,302,406,'tank'),('A010',0,578,404,'tank')]
out=[]
for bid,ts,u,v,kind in rows:
 b=bs[bid];p=poses[str(ts)];K=np.array([[p['focal'],0,800],[0,p['focal'],450],[0,0,1]],float);D=np.array([p['radial'],0,0,0,0]);R=np.array(p['rotation']);C=np.array(p['position']);q=cv2.undistortPoints(np.array([u,v],float).reshape(1,1,2),K,D).ravel();direction=np.r_[q,1]@R;offset=.72 if kind=='tank' else .3;z=b['roof_height']+offset;world=C+direction*(z-C[2])/direction[2];out.append(dict(building_id=bid,kind=kind,source_time=ts,source_pixel=[u,v],world_center=world.tolist(),evidence='Visible cylindrical rooftop fixture position from annotated source pixels. Size, support frame and functional label are inferred.'))
(root/'observed_roof_fixtures.json').write_text(json.dumps(out,indent=2));print('Positioned',len(out),'visible roof fixtures')
