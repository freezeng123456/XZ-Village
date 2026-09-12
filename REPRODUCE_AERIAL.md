# Reproduce the aerial continuation

Run from the repository root. The original MP4 is deliberately not included. The checked-in original landmark `.blend` is the input to the extension; it is never overwritten.

The validated environment was macOS arm64, Python 3.12, Blender 5.2.1, and the versions in `requirements-aerial.txt`. All computations ran locally on CPU. The forward-flight surface pipeline uses dense DIS correspondences, camera-based triangulation and explicit rejection gates; it is not COLMAP's CUDA dense MVS pipeline.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-aerial.txt
VILLAGE_VIDEO='/absolute/path/to/dji_fly_20260216_134446_0050_1771258754211_video.mp4'
VILLAGE_BLENDER='/Applications/Blender.app/Contents/MacOS/Blender'

.venv/bin/python work/inspect_aerial.py "$VILLAGE_VIDEO" --output work/aerial/reference
.venv/bin/python work/reconstruct_aerial.py "$VILLAGE_VIDEO" --output work/aerial/sfm
.venv/bin/python work/dense_flow_aerial.py work/aerial/sfm --start 0 --end 76
.venv/bin/python work/align_aerial.py
.venv/bin/python work/package_aerial.py
.venv/bin/python work/trace_site.py
.venv/bin/python work/fit_neighbour_roofs.py
"$VILLAGE_BLENDER" -b outputs/Village_Realistic_Target.blend --python work/build_aerial_continuation.py
.venv/bin/python work/build_viewer.py
"$VILLAGE_BLENDER" -b outputs/aerial-continuation/Village_Aerial_Continuation.blend --python work/validate_aerial_blend.py
```

The scripts select the largest registered model containing the 48-second landmark. Model IDs can change between runs. Do not combine disconnected models without a separately checked alignment. Exact point counts can vary across library versions or parallel executions; treat the included manifests as the evidence for this particular delivered snapshot.

`work/dense_aerial.py` is the earlier rectified-SGBM diagnostic route. It is retained for reproducibility of the investigation but is not consumed by the delivered surface package: several forward-flight pairs have unsuitable rectification and excessive disparity ranges. `work/inspect_blend.py` and `work/hash_landmark.py` are read-only audit helpers.

The HTML preview has no network dependency. To open it through a local browser URL:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory outputs/aerial-continuation
```

Open `http://127.0.0.1:8765/Village_Viewer.html`. The PLY and report links refer to the included release files. If running the modelling commands in a fresh checkout, use the release-copy step in `work/export_aerial_release.py` after validation to gather the supporting files.

Technical references: [COLMAP Python interface](https://colmap.github.io/pycolmap/index.html), [OpenCV camera calibration and triangulation](https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html). The code records the actual options used, rather than relying on unspecified default settings.
