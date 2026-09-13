"""Audit actual cross-flight tracks; separately report numerical and visual evidence."""
import argparse,json
from pathlib import Path
import numpy as np
import pycolmap as pc
import cv2

def flight(im):
    t=float(im.name[6:-4])
    return 'outbound' if t<=112 else ('return' if 240<=t<=270 else 'other')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('model',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    rec=pc.Reconstruction(a.model);images={i:im for i,im in rec.images.items() if im.has_pose};cross=[]
    for id,p in rec.points3D.items():
        obs=[(images[e.image_id],e.point2D_idx) for e in p.track.elements if e.image_id in images]
        fs={flight(im) for im,_ in obs}
        if {'outbound','return'}<=fs:
            cross.append(dict(id=id,error=p.error,xyz=p.xyz.tolist(),observations=[dict(image=im.name,xy=im.points2D[ix].xy.tolist()) for im,ix in obs]))
    camera_rows=[]
    for id,im in images.items():
        camera_rows.append(dict(name=im.name,flight=flight(im),center=im.projection_center().tolist(),R=im.cam_from_world().rotation.matrix().tolist(),T=im.cam_from_world().translation.tolist()))
    errors=np.array([p.error for p in rec.points3D.values()]);spatial=[]
    for name in ['frame_044.00.jpg','frame_256.00.jpg']:
        xy=np.array([o['xy'] for p in cross for o in p['observations'] if o['image']==name]);bins=[]
        if len(xy):bins=np.unique(np.floor(xy/[300,225]).astype(int),axis=0).tolist()
        spatial.append(dict(image=name,cross_flight_observations=len(xy),occupied_300x225_bins=bins))
    summary=dict(model=str(a.model),registered_images=len(images),points=rec.num_points3D(),cross_flight_points=len(cross),cross_flight_median_error=float(np.median([p['error'] for p in cross])) if cross else None,median_reprojection_error=float(np.median(errors)),p95_reprojection_error=float(np.percentile(errors,95)),images_by_flight={f:sum(flight(im)==f for im in images.values()) for f in ['outbound','return','other']},source_view_track_coverage=spatial,numerical_connectivity_gate=bool(len(cross)>=200 and any(flight(im)=='outbound' for im in images.values()) and any(flight(im)=='return' for im in images.values())),visual_alignment_reviewed=False)
    (a.out/'camera_audit.json').write_text(json.dumps(summary,indent=2));(a.out/'cross_flight_tracks.json').write_text(json.dumps(cross,indent=2));(a.out/'recovered_cameras.json').write_text(json.dumps(camera_rows,indent=2))
    for name in ['frame_044.00.jpg','frame_256.00.jpg']:
        src=Path('work/rebuild4/sfm/images')/name;im=cv2.imread(str(src))
        if im is None:continue
        for p in cross:
            for o in p['observations']:
                if o['image']==name:cv2.circle(im,tuple(np.round(o['xy']).astype(int)),4,(0,220,255),-1)
        cv2.imwrite(str(a.out/f'{Path(name).stem}_cross_tracks.jpg'),im,[cv2.IMWRITE_JPEG_QUALITY,94])
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
