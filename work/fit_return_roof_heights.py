"""Transfer main-model surface heights into manually calibrated return roofs.

Colour, visibility and roof-interior gates reduce cross-view contamination.
Ground height remains an architectural storey-height estimate, not a survey.
"""
from pathlib import Path
import json,cv2,numpy as np
from scipy.spatial import cKDTree
root=Path('work/buildings');path=root/'architecture_candidates.json';data=json.loads(path.read_text());ca=json.loads((root/'return_camera_roof_candidate.json').read_text());R=np.array(ca['rotation_world_to_camera']);T=np.array(ca['translation_world_to_camera']);C=np.array(ca['position']);K=np.array(ca['K']);D=np.array(ca['distortion']);rv=cv2.Rodrigues(R)[0];cloud=np.load('work/aerial/package/cloud.npz');xyz=cloud['xyz'];rgb=cloud['rgb'];pc=xyz@R.T+T;uv=cv2.projectPoints(xyz,rv,T,K,D)[0].reshape(-1,2);valid=(pc[:,2]>1)&np.isfinite(uv).all(1)&(uv[:,0]>1)&(uv[:,0]<1598)&(uv[:,1]>1)&(uv[:,1]<898);xyz=xyz[valid];rgb=rgb[valid];pc=pc[valid];uv=uv[valid];pix=np.round(uv).astype(int);idx=pix[:,1]*1600+pix[:,0];depth=np.full(1600*900,np.inf);np.minimum.at(depth,idx,pc[:,2]);src=cv2.imread('work/aerial/sfm/images/f256.00.jpg')[:,:,::-1];colour_error=np.linalg.norm(rgb.astype(float)-src[pix[:,1],pix[:,0]],axis=1);visible=(pc[:,2]<depth[idx]+1.2)&(colour_error<85)
summary=[]
for b in data['buildings']:
 if b['t']==256 and not b.get('height_locked'):
  poly=np.array(b['roof'],np.int32);mask=np.zeros((900,1600),np.uint8);cv2.fillPoly(mask,[poly],255);mask=cv2.erode(mask,np.ones((5,5),np.uint8));select=(mask[pix[:,1],pix[:,0]]>0)&visible;heights=xyz[select,2];support=len(heights)
  if support>=10:
   values,counts=np.unique(np.round(heights/.5),return_counts=True);mode=values[counts.argmax()]*.5;inl=np.abs(heights-mode)<1.5;roof=float(np.median(heights[inl]));spread=float(np.std(heights[inl]));num=int(inl.sum())
   if b['type']=='gable':roof-=.55
   if 3<roof<25:
    b['roof_height']=roof;b['roof_support']=num;b['roof_height_std']=spread;b['roof_height_evidence']='Main multi-view points projected through manual return camera; roof-interior, colour and depth gates; .55m estimated gable ridge-to-eave offset';norm=cv2.undistortPoints(np.array(b['roof'],float).reshape(-1,1,2),K,D).reshape(-1,2);rays=np.column_stack([norm,np.ones(len(norm))])@R;verts=C+rays*((roof-C[2])/rays[:,2])[:,None]
    if np.sum(verts[:,0]*np.roll(verts[:,1],-1)-verts[:,1]*np.roll(verts[:,0],-1))<0:verts=verts[::-1]
    b['roof_world']=verts.tolist()
  summary.append(dict(id=b['id'],height=round(b['roof_height'],2),support=b['roof_support']))
 # The observed roof is authoritative. Ground is estimated from stated storeys,
 # with a distinct provenance field so neither gets mistaken for surveyed data.
 story=3.15 if b['type']=='gable' else 3.35
 b['base_height']=max(-.25,b['roof_height']-b['floors']*story);b['base_height_evidence']=f'Estimated from roof altitude minus {b["floors"]} storeys at {story} nominal m; not recovered ground.'
anchors=[[*np.array(b['roof_world']).mean(0)[:2],b['base_height']] for b in data['buildings'] if b['roof_support']>0 or b.get('height_locked')]
anchors += [[0,0,0],[15,50,0],[0,160,.3],[15,-100,0]];anchors=np.array(anchors);tree=cKDTree(anchors[:,:2])
for b in data['buildings']:
 if b['t']!=256 or b['roof_support']>0 or b.get('height_locked'):continue
 for iteration in range(2):
  center=np.array(b['roof_world']).mean(0);dd,ix=tree.query(center[:2],k=min(6,len(anchors)));weights=1/np.maximum(dd,3)**2;base=float(weights@anchors[ix,2]/weights.sum());height=base+b['floors']*(3.15 if b['type']=='gable' else 3.35);norm=cv2.undistortPoints(np.array(b['roof'],float).reshape(-1,1,2),K,D).reshape(-1,2);rays=np.column_stack([norm,np.ones(len(norm))])@R;verts=C+rays*((height-C[2])/rays[:,2])[:,None]
  if np.sum(verts[:,0]*np.roll(verts[:,1],-1)-verts[:,1]*np.roll(verts[:,0],-1))<0:verts=verts[::-1]
  b['roof_world']=verts.tolist();b['roof_height']=height;b['base_height']=base
 b['roof_height_evidence']='No usable transferred roof points. Estimated storey height plus ground interpolated from neighbouring architectural bases.';b['base_height_evidence']='Estimated ground from neighbouring roof-derived storey bases; not surveyed or independently recovered.'
path.write_text(json.dumps(data,ensure_ascii=False,indent=2));(root/'ground_anchors_estimated.json').write_text(json.dumps(anchors.tolist(),indent=2));(root/'return_roof_height_transfer.json').write_text(json.dumps(summary,indent=2));print('Transferred roof support',sum(x['support']>0 for x in summary),'of',len(summary));print(json.dumps(summary[:15],indent=2))
