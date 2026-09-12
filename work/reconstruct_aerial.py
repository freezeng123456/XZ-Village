"""CPU multi-view reconstruction. Output has arbitrary scale until anchored.

The two frame ranges cover the village approach and return; the intervening
woodland/panorama and final descent are intentionally outside this model.
"""
import argparse, json, time
from pathlib import Path
import cv2
import numpy as np
import pycolmap

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); root=a.output; images=root/'images'
    images.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(str(a.video)); fps=cap.get(cv2.CAP_PROP_FPS)
    times=sorted(set(list(range(0,113,2))+list(range(244,271,2))))
    manifest=[]
    for t in times:
        name=f'f{t:06.2f}.jpg'; path=images/name
        if not path.exists():
            cap.set(cv2.CAP_PROP_POS_FRAMES,round(t*fps)); ok,f=cap.read()
            if not ok:raise RuntimeError(f'Decode failed at {t}')
            f=cv2.resize(f,(1600,900),interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(path),f,[cv2.IMWRITE_JPEG_QUALITY,96])
        manifest.append(dict(file=name,time_seconds=t,source_frame=round(t*fps)))
    cap.release()
    (root/'frames.json').write_text(json.dumps(manifest,indent=2)+'\n')
    db=root/'database.db'
    start=time.time()
    extraction=pycolmap.FeatureExtractionOptions(dict(num_threads=6,max_image_size=1600,
        sift=dict(max_num_features=6000)))
    matching=pycolmap.FeatureMatchingOptions(dict(num_threads=6))
    mapping=pycolmap.IncrementalPipelineOptions(dict(num_threads=6,random_seed=216,
        max_num_models=5,min_model_size=8,ba_global_max_num_iterations=40,
        ba_local_max_num_iterations=25,ba_global_frames_ratio=1.25,
        mapper=dict(init_min_tri_angle=8.0)))
    config=dict(pycolmap=pycolmap.__version__,width=1600,height=900,
        extraction=extraction.todict(),matching=matching.todict(),mapping=mapping.todict())
    (root/'config.json').write_text(json.dumps(config,indent=2,default=str)+'\n')
    print('EXTRACT',len(manifest),'frames',flush=True)
    pycolmap.extract_features(db,images,camera_mode=pycolmap.CameraMode.SINGLE,
        reader_options=dict(camera_model='SIMPLE_RADIAL'),extraction_options=extraction,
        device=pycolmap.Device.cpu)
    print('MATCH',flush=True)
    pycolmap.match_exhaustive(db,matching_options=matching,device=pycolmap.Device.cpu)
    print('MAP',flush=True)
    models=pycolmap.incremental_mapping(db,images,root/'sparse',options=mapping)
    summary=dict(input_frames=len(manifest),elapsed_seconds=time.time()-start,models=[])
    for idx,rec in models.items():
        dst=root/'sparse'/str(idx);rec.write(dst)
        rec.export_PLY(dst/'points.ply')
        errors=np.array([p.error for p in rec.points3D.values()])
        row=dict(id=idx,registered=rec.num_reg_images(),points=rec.num_points3D(),
            reprojection_error_mean=float(errors.mean()),reprojection_error_median=float(np.median(errors)),
            image_names=sorted(i.name for i in rec.images.values() if i.has_pose))
        summary['models'].append(row)
        print(json.dumps(row),flush=True)
    (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('DONE',flush=True)

if __name__=='__main__':main()
