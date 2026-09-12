# XZ Village · 去返程共同修订版

先打开 `Village_Review.html`，查看去程、返程对照、17 个重点修订单元与全部 297 个单元的双面图册。

`Village_Multiview_Refined.blend` 是可编辑模型。每个编号建筑保存在独立子集合中；进入编辑模式，用“选择相连元素”可选中独立的窗框、墙板、瓦片等构件。模型保留基准建筑；编号单元包含侧翼与屋顶单元，不代表住宅户数。

模型内没有照片纹理、照片铺地或相机背景。`reference/` 中的照片只是独立的检查资料。`RECONSTRUCTION_REPORT.md` 记录本次修改、验证范围与尚未解决的问题。

## 本地重建

已冻结本版参数与构建脚本。以本文件夹为工作目录，使用 Blender 5.2.1：

```sh
blender -b Village_Multiview_Refined.blend --python source/rebuild.py
```

结果写入 `rebuild/`，不会覆盖交付模型。脚本从交付场景保留基准建筑、灯光及相机，重新创建 297 个新增建筑单元。模型重建不需要原视频或外部图片；Blender 自带的 Python 与 NumPy 即可。其他 `source/` 脚本为原工作流程记录，其中的工作目录路径需要按环境调整。

几何与审阅资料均为本地交付；未进行远程发布。
