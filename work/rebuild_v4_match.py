"""Bounded CPU matching; retain the original feature database for provenance."""
import json, sqlite3, time
from pathlib import Path
import numpy as np
import pycolmap as pc

root=Path('work/rebuild4/sfm')
original=root/'database.db'
target=root/'bounded.db'
if not target.exists():
    src=sqlite3.connect(original);db=sqlite3.connect(target);src.backup(db);src.close()
    selection={}
    for iid,rows,cols,blob in db.execute('SELECT image_id,rows,cols,data FROM keypoints').fetchall():
        kp=np.frombuffer(blob,np.float32).reshape(rows,cols)
        _,dc,desc=db.execute('SELECT rows,cols,data FROM descriptors WHERE image_id=?',(iid,)).fetchone()
        desc=np.frombuffer(desc,np.uint8).reshape(rows,dc)
        # Balanced image coverage, retaining larger-scale features in every cell.
        scale=np.sqrt(np.abs(kp[:,2]*kp[:,5]-kp[:,3]*kp[:,4])) if cols==6 else kp[:,2]
        cell=np.minimum((kp[:,0]/150).astype(int),15)+16*np.minimum((kp[:,1]/150).astype(int),8)
        chosen=[]
        for c in range(144):
            ix=np.flatnonzero(cell==c)
            chosen.extend(ix[np.argsort(-scale[ix],kind='stable')[:56]].tolist())
        ix=np.array(sorted(chosen),np.int64)
        db.execute('UPDATE keypoints SET rows=?,data=? WHERE image_id=?',(len(ix),kp[ix].tobytes(),iid))
        db.execute('UPDATE descriptors SET rows=?,data=? WHERE image_id=?',(len(ix),desc[ix].tobytes(),iid))
        selection[str(iid)]=dict(original_count=rows,retained_count=len(ix),original_indices=ix.tolist())
    db.execute('DELETE FROM matches');db.execute('DELETE FROM two_view_geometries');db.commit()
    (root/'feature_selection.json').write_text(json.dumps(selection))
    db.execute('VACUUM');db.close()
db=sqlite3.connect(target)
frames=sorted([(n,float(n[6:-4])) for (n,) in db.execute('SELECT name FROM images')],key=lambda r:r[1]);db.close()
pairs=[]
for i,(n,t) in enumerate(frames):
    for m,s in frames[i+1:]:
        adjacent=s-t<=18
        cross=t<=114 and 232<=s<=272
        turn=96<=t<=150 and 210<=s<=244
        if adjacent or cross or turn:pairs.append((0 if adjacent else 1,abs(s-t),n,m))
pairs.sort()
pairpath=root/'bounded_pairs.txt';pairpath.write_text(''.join(f'{n} {m}\n' for _,_,n,m in pairs))
opts=pc.FeatureMatchingOptions(dict(num_threads=3,guided_matching=False,max_num_matches=10000))
(root/'bounded_matching_config.json').write_text(json.dumps(dict(pair_count=len(pairs),selection='16x9 cells, 56 largest scale features per cell',options=opts.todict()),indent=2,default=str))
print('MATCH_START',len(pairs),flush=True);start=time.time()
pc.match_image_pairs(target,matching_options=opts,pairing_options=dict(block_size=160,match_list_path=pairpath),device=pc.Device.cpu)
print('MATCH_DONE',time.time()-start,flush=True)
