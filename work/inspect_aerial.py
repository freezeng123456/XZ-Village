"""Extract timestamped, source-hashed reference frames without copying the video."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
from PIL import Image, ImageDraw

def main():
    p = argparse.ArgumentParser()
    p.add_argument('video', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise RuntimeError('Cannot open source video')
    fps, count = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    meta = dict(source_name=args.video.name, bytes=args.video.stat().st_size,
                fps=fps, frames=count, duration_seconds=count/fps,
                width=int(cap.get(3)), height=int(cap.get(4)))
    print(json.dumps(meta), flush=True)
    digest = hashlib.sha256()
    with args.video.open('rb') as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b''):
            digest.update(chunk)
    meta['sha256'] = digest.hexdigest()
    times = sorted(set([round(i*(count/fps-1)/19, 2) for i in range(20)] + [45,48,63,261]))
    sheet = Image.new('RGB', (1920, ((len(times)+3)//4)*294), '#171d21')
    draw = ImageDraw.Draw(sheet)
    meta['references'] = []
    for i,t in enumerate(times):
        if t >= count/fps: continue
        idx = round(t*fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok: raise RuntimeError(f'Cannot decode frame {idx}')
        name = f'frame_{idx:06d}_{t:07.2f}s.jpg'
        cv2.imwrite(str(out/name),frame,[cv2.IMWRITE_JPEG_QUALITY,95])
        thumb = Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
        thumb.thumbnail((480,270))
        x,y=(i%4)*480,(i//4)*294
        sheet.paste(thumb,(x,y))
        draw.text((x+10,y+274),f'{t:.2f}s | frame {idx}',fill='white')
        meta['references'].append(dict(time_seconds=t,frame_index=idx,file=name))
        print(name, flush=True)
    sheet.save(out/'contact_sheet.jpg',quality=93)
    (out/'source_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    cap.release()

if __name__ == '__main__': main()
