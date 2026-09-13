# V4 阶段存档与接续记录

日期：2026-09-13。当前安排为上传已有成果到 GitHub，然后暂停后续建模。本存档不表示所有建筑已达到最终质量目标。

## 冻结交付

当前交付目录为 `outputs/rebuilt-v4/`。该目录与已交付的 `XZ-Village-Rebuilt-V4.zip` 内容对应，保留原有文件名、数据和校验清单。完整压缩包放在 `v4-rebuild-checkpoint-20260913` 的 Release 附件中。

- 建筑及附属单元：402，包含主体、侧翼、雨棚和屋顶房，不等同于独立住宅数量。
- 主模型：`outputs/rebuilt-v4/Village_Rebuilt_Master.blend`。
- 交互模型：`outputs/rebuilt-v4/Village_Rebuilt_Web.glb`。
- 查看器与审阅：`Village_Viewer.html`、`Source_Comparison.html`、`Building_Catalogue.html`、`Pilot_Review.html`。
- 冻结输入：`data/architecture_geometry.json`、`data/architecture_profiles.json`、`data/village_environment.json`、`data/coordinate_system.json`。
- 检查记录：`evidence/`、`QUALITY.md`、`MANIFEST.json`、`SHA256SUMS.txt`。
- 完整压缩包：178,884,876 字节，512 个文件，SHA-256 `9b1dae1dfc04e71990cb8ac814e98763c88606157003c138de37abd9d83cf449`。

## 已验证的边界

去程与返程在同一相机模型中，注册 160 帧，含去程 57 帧和返程 31 帧。全局重投影误差中位数 0.606 px，跨航段中位数 0.771 px。六帧留出图像检查通过。这些数据检验相机和匹配特征的一致性，不能证明建筑没有遗漏。

已从冻结交付数据实际生成过新模型，402 个单元的编号、构件、门窗和网格顶点构建记录一致。原片照片没有作为主模型贴图。26 页双视图覆盖当前 402 个单元，7 个最终原片机位对照已查看；这些是建模 agent 自检，没有独立人员逐栋验收。

本机 HTTP 查看器已实际验证搜索、隔离、恢复、机位和环境开关，以及图册筛选和原片透明叠加。自动浏览器禁止 `file://`，直接双击 HTML 的方式未验证。

## 下次从哪里继续

先比较 44 秒与 256 秒同机位图，处理密集老屋之间的院落边房、院墙、连接体与残留空隙，再检查简化立面和远景单元。修改一处后，应返回去程和返程同机位确认轮廓、体量、间距和遮挡关系。不要依据编号数量、构件数量或相机误差宣布外观完成。

保留源图能确认的细节与推断的区别。当前绝对尺度未用实测长度校准；隐藏表面、部分屋面坡度和小设备有简化或推断。完整限制见交付目录中的 `QUALITY.md`。

要重新生成已冻结的模型，在仓库根目录运行：

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 4 --python outputs/rebuilt-v4/rebuild/rebuild_v4_build_architecture.py
```

结果写入 `outputs/rebuilt-v4/data/rebuilt_from_data/`。这只复建冻结场景，不重新计算原视频相机或稠密点云；主文件不会被此命令覆盖。测试环境是 Blender 5.2.1，脚本使用其内置 Python 和 NumPy。

`work/rebuild_v4_*.py` 保留相机、清单、几何、立面、环境、对照和打包流程的制作脚本；其中部分含制作时的本机路径。直接复建应优先用交付目录中的可移植脚本。原始视频、提取帧、摄影测量数据库、稠密中间数据、虚拟环境及日志仍保留在本机，不作为本次上传附件。

`work/REBUILD_V4_PROTOCOL.md` 与 `work/REBUILD_V4_CAMERA_RESULT.md` 是各阶段当时的记录，可能保留当时的待完成状态；当前状态以本文件和交付质量说明为准。
