# XZ Village — editable architectural reconstruction

The current deliverable completes 299 inventoried architectural units around the retained original landmark, for 300 numbered units including connected wings and small ancillary structures. Video-observed placement and source colours are combined with user-authorized estimates of hidden dimensions and details.

- [Final editable Blender scene](outputs/building-quality/Village_Reconstructed.blend)
- [Searchable source and dual-view building review](outputs/building-quality/Village_Review.html)
- [Chinese scope and verification report](outputs/building-quality/RECONSTRUCTION_REPORT.md)
- [Architectural pipeline and reproduction boundaries](REPRODUCE_ARCHITECTURE.md)

This is an architectural visualization, with approximate terrain and landscape context. Physical dimensions and unseen real-world details are not survey-verified. The earlier point-cloud continuation below is retained as historical evidence.

## Earlier September 12 aerial continuation

The new editable project is [`outputs/aerial-continuation/Village_Aerial_Continuation.blend`](outputs/aerial-continuation/Village_Aerial_Continuation.blend). It retains the original landmark and adds a multi-view reconstruction of the approach segment, 10 separately labelled neighbouring structural drafts, and traced pond/bridge elements.

- [Interactive point-cloud preview](outputs/aerial-continuation/Village_Viewer.html), self-contained and usable offline.
- [Chinese scope, evidence and validation report](outputs/aerial-continuation/RECONSTRUCTION_REPORT.md).
- [Reproduction commands](REPRODUCE_AERIAL.md).

The current dataset registers 57 approach frames into the main coordinate system. The 14 return frames form a separate reconstruction and are preserved as evidence, not silently merged. The working scale still inherits the old **estimated** 7.5 m landmark roof width. Approximate structural drafts and camera-dependent appearance are separate from observed surface patches. Holes, incomplete facades and rough geometry remain visible.

## Original landmark baseline

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
