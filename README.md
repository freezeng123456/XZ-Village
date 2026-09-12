# XZ Village — Blender reconstruction

This repository contains the completed Blender reconstruction work based on the supplied aerial village video.

The main deliverable is [`outputs/Village_Realistic_Target.blend`](outputs/Village_Realistic_Target.blend). It focuses on the beige, three-storey landmark building at the village edge, with editable geometry for its facade panels, windows, terrace, railings, roof paving, rooftop equipment and front yard.

## Deliverables

| File | Purpose |
| --- | --- |
| [`outputs/Village_Realistic_Target.blend`](outputs/Village_Realistic_Target.blend) | Editable Blender 5.2 landmark-building project with embedded reference images |
| [`outputs/Target_Reference_Comparison.jpg`](outputs/Target_Reference_Comparison.jpg) | Source-frame and reconstructed-building comparison |
| [`outputs/Target_Realistic_Closeup.png`](outputs/Target_Realistic_Closeup.png) | Close-up render from the calibrated aerial viewpoint |
| [`outputs/Target_Geometry_Check.png`](outputs/Target_Geometry_Check.png) | Clay render for checking the modeled geometry |
| [`outputs/Village_Reference_View.png`](outputs/Village_Reference_View.png) | Village-scale reference viewpoint |
| [`outputs/重点建筑重建说明.txt`](outputs/重点建筑重建说明.txt) | Chinese notes on scope, precision and limitations |

The earlier broad village study is also included as `outputs/Village_Reconstruction.blend` with its overview renders.

## Model scope

The landmark building was manually matched to the 45–48 second part of the aerial video. Its nominal width, depth and height are visual estimates, because there is no survey or known physical scale in the footage. The neighboring village context is arranged from the video view and includes photo-projected elements; it is best viewed from the provided reference camera rather than treated as a complete survey-grade model.

To continue toward a full precise reconstruction, add at least one real-world dimension and clear front, rear and side photos for each building or a dense drone survey.

## Opening the project

Open the main `.blend` file in Blender 5.2 or a compatible later release. The project includes four cameras:

1. Calibrated landmark-building reference view
2. Village reference view
3. Road-side geometry inspection view
4. Roof inspection view

The original drone video is deliberately excluded from this repository because of its size and because it is source material rather than an output artifact.

## Scripts

The `work/` folder contains the reproducible Python scripts used for frame extraction, video-camera calibration, geometry construction, texture cleanup and rendering. Generated preview frames, virtual environments, logs and the source video are excluded.
