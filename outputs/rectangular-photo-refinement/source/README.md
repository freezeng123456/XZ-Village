# 重建脚本与输入

本交付目录中的 inventory.json、profiles.json 和 final_alignment_audit.json 是冻结输入；Village_Rectangular_Refined.blend 提供去除照片覆层后的基准建筑、相机和真实建模构件，不包含照片地面或投影背景。

在有 Blender 5.2.1 的机器上，用系统 Python 运行：

```sh
python3 source/rebuild_architecture_v2.py --blender /Applications/Blender.app/Contents/MacOS/Blender --output /absolute/path/to/Rebuilt
```

脚本在临时工作目录生成全部建筑，重新载入结果并执行结构核验。输出包含候选模型、构件清单和 validation.json。改动 profiles.json 后的外观必须重新渲染审阅；结构通过不能自动视为照片对齐通过。

其余脚本保留拟合、标注修订和检查流程，运行它们需要原仓库 work/buildings 下的原视频帧、相机 poses、V1 标注及观测配置。它们不属于上述冻结输入重建命令的依赖。
