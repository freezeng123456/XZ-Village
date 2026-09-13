# 从交付数据重新生成模型

此目录包含最终几何和程序材质的 Blender 生成代码。`../data/` 中的建筑、立面和环境数据已经冻结，生成模型不需要原视频、摄影测量数据库或联网。

在 Blender 的 Scripting 工作区打开 `rebuild_v4_build_architecture.py` 并运行；或在解压后的目录执行：

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 4 --python rebuild/rebuild_v4_build_architecture.py
```

新结果写到 `data/rebuilt_from_data/`，包括 `architecture.blend` 和对应机位图。此命令会清空当前 Blender 场景，因此在空白 Blender 进程运行。它不改写本包的 `Village_Rebuilt_Master.blend`。

本次主文件使用 Blender 5.2.1 生成。脚本使用 Blender 内置 Python 和 NumPy；其他 Blender 版本未测试。

摄影测量的相机质量证据在 `../evidence/`；此脚本仅重建已经整理好的场景，不重新计算原视频相机与稠密点云。
