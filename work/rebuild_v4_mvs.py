"""Convert a verified SfM component to CPU OpenMVS, with no decorative inputs."""
import argparse,json,subprocess,time
from pathlib import Path
import pycolmap as pc

def main():
    ap=argparse.ArgumentParser();ap.add_argument('model',type=Path);ap.add_argument('--name',default='surface');ap.add_argument('--max-resolution',type=int,default=1600);ap.add_argument('--threads',type=int,default=6);ap.add_argument('--views',type=int,default=5);ap.add_argument('--images',nargs='*');ap.add_argument('--prepare-only',action='store_true');a=ap.parse_args()
    repo=Path.cwd();dest=(repo/'work/rebuild4'/a.name).resolve();dest.mkdir(parents=True,exist_ok=True);model=a.model.resolve();tools=(repo/'work/rebuild4/tools/openmvs').resolve();images=(repo/'work/rebuild4/sfm/images').resolve();start=time.time()
    pc.undistort_images(dest,model,images,image_names=a.images or [],undistort_options=dict(max_image_size=2400),num_threads=a.threads,jpeg_quality=97)
    with (dest/'import.log').open('w') as log:
        subprocess.run([str(tools/'InterfaceCOLMAP'),'-i',str(dest),'-o',str(dest/'scene.mvs'),'--image-folder',str(dest/'images'),'--max-threads',str(a.threads)],cwd=dest,stdout=log,stderr=subprocess.STDOUT,check=True)
    cmd=[str(tools/'DensifyPointCloud'),str(dest/'scene.mvs'),'-o',str(dest/'scene_dense.mvs'),'--resolution-level','0','--max-resolution',str(a.max_resolution),'--min-resolution','640','--number-views',str(a.views),'--number-views-fuse','3','--max-threads',str(a.threads),'--iters','4','--geometric-iters','2','--tower-mode','0','--estimate-roi','0','--crop-to-roi','0','--postprocess-dmaps','1']
    (dest/'run_config.json').write_text(json.dumps(dict(model=str(model),command=cmd,input_images=a.images,elapsed_prepare_seconds=time.time()-start),indent=2))
    if a.prepare_only:return
    print('DENSE_START',dest,flush=True)
    with (dest/'dense.log').open('w') as log:subprocess.run(cmd,cwd=dest,stdout=log,stderr=subprocess.STDOUT,check=True)
    pcl=dest/'scene_dense.ply';assert pcl.exists() and pcl.stat().st_size>10000
    (dest/'done.json').write_text(json.dumps(dict(elapsed_seconds=time.time()-start,pointcloud_bytes=pcl.stat().st_size),indent=2));print('DENSE_FINISHED',pcl.stat().st_size,flush=True)

if __name__=='__main__':main()
