"""Prompted roof tracing from fresh manual source boxes, with explicit review status."""
import os,sys,json,time,numpy as np,cv2
from pathlib import Path
sys.path.insert(0,str(Path('work/rebuild4/tools/onnx_runtime').resolve()))
import onnxruntime as ort
P=Path('work/rebuild4');OUT=P/'architecture/census_masks';OUT.mkdir(exist_ok=True);opt=ort.SessionOptions();opt.intra_op_num_threads=3;opt.inter_op_num_threads=1;enc=ort.InferenceSession(str(P/'tools/efficientsam_ti_encoder.onnx'),opt,providers=['CPUExecutionProvider']);dec=ort.InferenceSession(str(P/'tools/efficientsam_ti_decoder.onnx'),opt,providers=['CPUExecutionProvider']);entries=json.loads((P/'architecture/census_box_annotations.json').read_text())['entries'];cache={};images={};results=[];start=time.time()
for e in entries:
 name=e['source_image'];bid=e['id'];saved=OUT/(bid+'.png')
 if name not in images:images[name]=cv2.imread(str(P/'sfm/images'/name))
 image=images[name];box=np.array(e['search_box_px'],float).reshape(2,2);box[0]=np.maximum(box[0],[0,0]);box[1]=np.minimum(box[1],[2399,1349]);ctr=box.mean(0);x0=min([0,700,1400],key=lambda x:abs((x+500)-ctr[0]));y0=min([0,450],key=lambda y:abs((y+450)-ctr[1]));key=(name,x0,y0)
 if key not in cache:
  tile=image[y0:y0+900,x0:x0+1000];emb=enc.run(None,{'batched_images':tile[...,::-1].transpose(2,0,1)[None].astype(np.float32)/255})[0];cache[key]=(emb,tile.shape[:2]);print('ENCODE',key,flush=True)
 emb,size=cache[key];points=(box-np.array([x0,y0])).astype(np.float32);points[0]=np.maximum(points[0],0);points[1]=np.minimum(points[1],np.array(size)[::-1]-1);coords=list(points);labels=[2,3]
 for point in e.get('positive_points',[]):coords.append(np.array(point)-[x0,y0]);labels.append(1)
 for point in e.get('negative_points',[]):coords.append(np.array(point)-[x0,y0]);labels.append(0)
 pred,score,*_=dec.run(None,{'image_embeddings':emb,'batched_point_coords':np.array([[coords]],np.float32),'batched_point_labels':np.array([[labels]],np.float32),'orig_im_size':np.array(size,np.int64)});candidate_masks=pred[0,0]>0;candidate_scores=score[0,0];best=int(np.argmax(candidate_scores));mask=candidate_masks[best].astype(np.uint8);cont,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);clean=np.zeros(mask.shape,np.uint8)
 if cont:
  largest=max(cont,key=cv2.contourArea);cv2.drawContours(clean,[largest],-1,1,-1);contour=cv2.approxPolyDP(largest,1.15,True)[:,0,:]+[x0,y0]
 else:contour=np.empty((0,2),int)
 full=np.zeros((1350,2400),np.uint8);full[y0:y0+size[0],x0:x0+size[1]]=clean;cv2.imwrite(str(saved),full*255);bmask=np.zeros_like(full);cv2.rectangle(bmask,tuple(box[0].astype(int)),tuple(box[1].astype(int)),1,-1);area=int(full.sum());inside=int((full*bmask).sum());outside=1-inside/max(1,area);result=dict(**e,mask_path=str(saved),mask_area_px=area,polygon_px=contour.tolist(),sam_score=float(candidate_scores[best]),mask_outside_box_fraction=outside,review_status='unreviewed; source box and mask do not prove main-body identity or coverage',flags=[])
 if area<100:result['flags'].append('very_small_mask')
 if outside>.14:result['flags'].append('mask_extends_beyond_search_box')
 if float(candidate_scores[best])<.65:result['flags'].append('low_mask_score')
 if e['partial_image_boundary']:result['flags'].append('incomplete_source_boundary')
 results.append(result)
 if len(results)%20==0:print('MASKS',len(results),'elapsed',round(time.time()-start,1),flush=True)
(OUT/'manifest.json').write_text(json.dumps(dict(entries=results,status='source mask proposals awaiting visual review',elapsed=time.time()-start),indent=2))
for name,image in images.items():
 overlay=image.copy()
 for i,e in enumerate(results):
  if e['source_image']!=name:continue
  mask=cv2.imread(e['mask_path'],0)>0;color=cv2.cvtColor(np.uint8([[[i*41%180,190,255]]]),cv2.COLOR_HSV2BGR)[0,0];overlay[mask]=(overlay[mask]*.65+color*.35).astype(np.uint8);cont,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(overlay,cont,-1,tuple(int(x) for x in color),2);c=np.array(e['search_box_px']).reshape(2,2).mean(0).astype(int);cv2.putText(overlay,e['id'],tuple(c),cv2.FONT_HERSHEY_SIMPLEX,.48,(0,0,0),3);cv2.putText(overlay,e['id'],tuple(c),cv2.FONT_HERSHEY_SIMPLEX,.48,(255,255,255),1)
 cv2.imwrite(str(OUT/(name[:-4]+'_overlay.jpg')),overlay,[cv2.IMWRITE_JPEG_QUALITY,96])
print('DONE',len(results),flush=True)
