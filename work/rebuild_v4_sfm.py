"""Fresh full-flight reconstruction. Never imports the rejected building inventory."""
import argparse
import hashlib
import json
import time
from pathlib import Path
import cv2
import numpy as np
import pycolmap as pc

ROOT=Path('work/rebuild4')
VIDEO=Path('/Users/zenghang/Desktop/dji_fly_20260216_134446_0050_1771258754211_video.mp4')

def save(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n')

def extract():
    root=ROOT/'sfm';images=root/'images';images.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(str(VIDEO));fps=cap.get(cv2.CAP_PROP_FPS)
    times=sorted(set(list(range(0,272,2))+list(range(272,325,4))+list(range(241,270,2))+[325]))
    manifest=[]
    for i,t in enumerate(times):
        path=images/f'frame_{t:06.2f}.jpg'
        if not path.exists():
            candidates=[]
            for dt in [0,-.15,.15]:
                fr=max(0,min(9759,round((t+dt)*fps)))
                cap.set(cv2.CAP_PROP_POS_FRAMES,fr);ok,f=cap.read()
                if not ok:continue
                gray=cv2.cvtColor(cv2.resize(f,(960,540)),cv2.COLOR_BGR2GRAY)
                sharp=float(cv2.Laplacian(gray,cv2.CV_32F).var())
                candidates.append((sharp,fr,f))
            if not candidates:raise RuntimeError(f'Could not decode {t}')
            sharp,fr,f=max(candidates,key=lambda x:x[0])
            small=cv2.resize(f,(2400,1350),interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(path),small,[cv2.IMWRITE_JPEG_QUALITY,97])
            row=dict(file=path.name,nominal_seconds=t,source_frame=fr,actual_seconds=fr/fps,sharpness_laplacian_960=sharp,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            save(root/'frame_metadata'/f'{path.stem}.json',row)
        else:row=json.loads((root/'frame_metadata'/f'{path.stem}.json').read_text())
        manifest.append(row)
        if i%10==0:print('EXTRACTED',i+1,len(times),'at',t,flush=True)
    cap.release();save(root/'frames.json',manifest)
    save(ROOT/'source.json',dict(path=str(VIDEO),bytes=VIDEO.stat().st_size,width=3840,height=2160,fps=fps,duration_seconds=9760/fps,prior_verified_sha256='7ca8636aa921d60bcb9a3837d70fd060c306b808c1d0c6098cd9b473fe9f9a65',prior_model_geometry_used=False))
    return root,images,manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--extract-only',action='store_true');ap.add_argument('--map-only',action='store_true');ap.add_argument('--database',default='database.db');ap.add_argument('--sparse-dir',default='sparse');a=ap.parse_args()
    root,images,manifest=extract()
    if a.extract_only:return
    db=root/a.database;start=time.time()
    ext=pc.FeatureExtractionOptions(dict(num_threads=6,max_image_size=2400,sift=dict(max_num_features=16000,peak_threshold=.004)))
    match=pc.FeatureMatchingOptions(dict(num_threads=6,guided_matching=True,max_num_matches=40000))
    mapper=pc.IncrementalPipelineOptions(dict(num_threads=6,random_seed=913,max_num_models=8,min_model_size=10,ba_global_frames_ratio=1.25,ba_global_max_num_iterations=60,ba_local_max_num_iterations=30,mapper=dict(init_min_tri_angle=8,abs_pose_max_error=6,filter_max_reproj_error=3)))
    save(root/(a.sparse_dir+'_config.json'),dict(pycolmap=pc.__version__,database=str(db),extraction=ext.todict(),matching=match.todict(),mapping=mapper.todict()))
    if not a.map_only:
        print('FEATURES',len(manifest),flush=True)
        pc.extract_features(db,images,camera_mode=pc.CameraMode.SINGLE,reader_options=dict(camera_model='SIMPLE_RADIAL'),extraction_options=ext,device=pc.Device.cpu)
        print('MATCH_EXHAUSTIVE',flush=True)
        pc.match_exhaustive(db,matching_options=match,device=pc.Device.cpu)
    print('MAPPING',flush=True)
    recs=pc.incremental_mapping(db,images,root/a.sparse_dir,options=mapper)
    summary=dict(input_frames=len(manifest),elapsed_seconds=time.time()-start,models=[])
    for idx,rec in recs.items():
        dest=root/a.sparse_dir/str(idx);rec.write(dest);rec.export_PLY(dest/'points.ply')
        names=sorted(im.name for im in rec.images.values() if im.has_pose)
        ts=[float(n[6:-4]) for n in names]
        row=dict(id=idx,registered=rec.num_reg_images(),points=rec.num_points3D(),mean_reprojection_error=rec.compute_mean_reprojection_error(),forward_frames=sum(t<=112 for t in ts),return_frames=sum(240<=t<=270 for t in ts),connecting_frames=sum(112<t<240 for t in ts),image_names=names,cameras=[c.todict() for c in rec.cameras.values()])
        summary['models'].append(row);print('MODEL',idx,'REGISTERED',len(names),'FORWARD',row['forward_frames'],'RETURN',row['return_frames'],flush=True)
    save(root/(a.sparse_dir+'_summary.json'),summary);print('SFM_COMPLETE',flush=True)

if __name__=='__main__':main()
