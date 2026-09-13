# Reconstruction route and host verification

Checked 2026-09-13 directly by the working agent. This is a method and runtime check, not independent reconstruction validation.

The [COLMAP tutorial](https://colmap.github.io/tutorial.html) separates camera/sparse reconstruction from dense multi-view stereo. The dense stage must follow a consistent camera solution; disjoint models are separate components, not proof that two flights share one coordinate system.

The [COLMAP FAQ](https://colmap.github.io/faq.html#available-functionality-without-gpu-cuda) states that its dense reconstruction requires CUDA, while sparse reconstruction can run on CPU and external dense reconstruction is an alternative. The local pycolmap 4.2.0 runtime reports has_cuda=False. CPU extraction, matching, incremental and global mapping APIs are present.

[OpenMVS build documentation](https://github.com/cdcseacave/openMVS/wiki/Building) lists CUDA as optional and publishes macOS arm64 binaries. The [v2.4.0 release](https://github.com/cdcseacave/openMVS/releases/tag/v2.4.0) contains OpenMVS_macOS_arm64.zip. The artifact was downloaded into the task's ignored work directory; DensifyPointCloud and InterfaceCOLMAP both ran successfully on the Apple M4 Pro/48 GB host. This verifies executable startup only, not a successful reconstruction.

The installed InterfaceCOLMAP help requires COLMAP's undistorted PINHOLE images. The installed DensifyPointCloud exposes CPU thread limits, view-neighbor selection, photometric and geometric iterations, and multi-view fusion thresholds. Camera/geometry audit precedes conversion, and depth maps must be recomputed after camera geometry changes.

OpenMVS will provide a multi-view surface reference. Raw noisy geometry, vertex count, image-like colored surfaces, and image textures are not substitutes for the requested editable, source-aligned architecture. Roof, wall, ground and connected-wing interpretation must be checked against source imagery.
