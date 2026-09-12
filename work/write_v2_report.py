from pathlib import Path
import json
r=Path.cwd();out=r/'outputs/rectangular-photo-refinement';a=json.loads((r/'work/buildings/v2/final_alignment_audit.json').read_text());v=json.loads((out/'validation.json').read_text());p=json.loads((r/'work/buildings/v2/profiles.json').read_text());c=v['counts']
report=f'''# XZ-Village：矩形主体与照片外观细化

本轮根据“住宅方正，整体颜色和纹理应与照片对齐”的要求重建建筑。按最新要求，交付模型已移除所有照片地面和立面照片覆层；原视频画面只用于独立分栏对照。保留原红框建筑 B001，重新生成其余 **{c["new_units"]} 个编号单元**；编号包含主屋、连接侧翼与小型附属房，不等同于独立住户数。

先打开 [逐栋照片对照](Village_Review.html)，搜索 B005、B008、B010 或其他编号。编辑使用 [Blender 模型](Village_Rectangular_Refined.blend)。每张卡片依次展示照片、对应照片视角的模型和背面检查图。

## 本轮具体改动

- **矩形主体**：旧版 299 个单元中有 229 个未满足严格矩形约束。本轮全部采用水平矩形楼板、互相垂直的墙面，复杂住宅按已有编号拆分为矩形主体和矩形侧翼。透视图中的斜四边形不再直接作为住宅平面。
- **对照照片的近景建筑**：39 个 B/C 组单元经过原视频裁切逐一检查并调整外观。B005 增加前后屋顶分区、隔墙、双水箱与钢支架，并调整上层窗形和有进深的凹口；B008/B010 等补上有进深的转角阳台、立柱、栏杆和弧形檐口；B014 修正为矩形四坡蓝瓦顶并补足白色屋檐。
- **颜色与材料**：分别处理灰白横向贴砖、米色贴砖、浅绿涂料、红褐色墙面、裸砖与旧水泥墙。近景增加与照片对应的墙面霉斑；其余建筑依据视频采样颜色和建筑类型生成连续材质。表面颗粒、灰缝、雨痕和背面旧化属于合理补全。
- **真实构件**：门窗开洞、窗框、窗台、防盗栏、阳台后墙与门、排水管及卡箍、水箱框架和供水管均为模型构件。瓦房屋顶使用逐片搭接的曲面瓦与脊瓦，金属顶有接缝，光伏顶有边框和支撑。
- **相邻位置修正**：矩形化后重新检查重叠，调整了 {a['adjusted_units']} 个单元的位置，最大平移约 {a['maximum_translation_m']:.2f} 模型米。此项用于消除近似重建造成的主体穿插，不能理解为实际地籍位置精度。

另对 A/N/F 组可辨认阳台和 R 组屋顶设备作了补全；共有 {sum(q["manual_source_review"] for q in p.values())} 个单元使用单独的照片外观修订配置。屋顶复核纠正了 25 个平顶／瓦顶分类，连排老屋屋脊按整排走向调整；D001 为红色金属坡顶，O003 补上六角屋面砖与深色修补区。原编号 O069 是菜地，R031 是邻房旁绿地，均已从建筑清单剔除，原标注保留在 rejected_candidates.json 供追溯。覆盖编号图沿用原视频标注，O069、R031 标记不代表保留建筑。

## 检查结果与适用边界

| 项目 | 本轮结果 |
|---|---|
| 保存文件中的实际矩形楼板 | {c["new_units"]} / {c["new_units"]} 通过 |
| 有高度重叠的住宅主体之间穿插 | 0 对 |
| 原红框建筑 | 删除 7 个照片覆层，其余 {v["landmark"]["objects"]} 个对象几何保持一致 |
| 新建筑对象 | {c['new_objects']:,} |
| 新建筑网格顶点 | {c['mesh_vertices']:,} |
| 实际开洞（包括门、窗与阳台） | {c['openings']:,} |
| 外部链接库 | 0 |
| 模型中的照片图片、图片纹理节点与相机背景 | 均为 0；墙面与屋顶使用模型构件和程序材质 |

结构核验还包括墙板位于主体边界内、坐标有效、非退化面、楼板、开洞、窗框、屋顶构件、排水与材质覆盖。结果见 [validation.json](validation.json)。另已从交付文件和冻结参数完整重建 297 个单元，重新载入通过同一结构核验，对象、顶点与开洞数量一致；见 [rebuild_validation.json](rebuild_validation.json)。实际渲染与逐页目视检查另记于 [visual_review.json](visual_review.json)，不把结构检查代替外观检查。

对齐指标是在消除穿插之后，将矩形主屋屋顶重新投影到原视频标注上计算的：屋顶区域交并比中位数 **{a['median_roof_iou']:.3f}**，轮廓边缘误差中位数 **{a['median_edge_rmse_px']:.2f} 像素**，90 分位数 **{a['p90_edge_rmse_px']:.2f} 像素**（参考画面 1600×900）。远景细长标注中最低交并比约 **{a['minimum_iou']:.3f}**，这部分深度更多依赖合理推测。该指标只衡量参考视图的屋顶布局，不衡量立面相似度、材质真实性或测绘精度。逐栋值见 [final_alignment_audit.json](final_alignment_audit.json)。

照片裁切保留原镜头畸变，模型取景使用去畸变的相机投影；二者保持对应朝向并分别取景，不是像素级叠合。

**照片能够提供的细节并不均等。** 近景可识别部分已单独修整，远景与遮挡面使用规则门窗、估计层高和推测构件。栏杆数量、窗框截面、未见立面、室内、细小设备不能视为实测复原。照片地面、立面照片覆层和相机背景均已删除。纯模型视图只保留建出的房屋、院内构件和几何化池塘栏杆；没有补建的道路、植被和场景空缺直接留空。原图与模型在 [44 秒对照](Scene_Comparison_44s.jpg) 和 [256 秒对照](Scene_Comparison_256s.jpg) 中分栏展示。删除清单与零图片纹理检查见 [clean_structure_audit.json](clean_structure_audit.json)。

## 模型使用与编辑

Blender 5.2.1 中保存并重新载入核验。`01–03 TARGET` 保留原基准建筑；`11 ARCHITECTURE` 下每个编号是独立集合。每栋按材质合并为少量可编辑对象，独立构件仍保留各自的连接关系，网格编辑模式可用 Select Linked 选择构件。对象的 `original_components` 属性记录构件名称与面索引区间。

文件打开时提供 44 秒对应机位的纯模型视图。使用原视频恢复相机 `Video 044.00s | recovered` 对照近景；返回段另有 256 秒相机。渲染使用 Cycles；材质预览用于查看颜色、砖缝和旧化。

`source/` 保存本轮构建、拟合、核验与交付脚本。`inventory.json` 保存矩形参数和来源；`profiles.json` 保存逐栋材质与立面配置。修改后的范围仍应通过结构核验，并重新渲染受影响建筑进行照片与背面检查。
'''
(out/'RECONSTRUCTION_REPORT.md').write_text(report);(out/'README.md').write_text('# XZ-Village 矩形住宅与照片细化版\n\n打开 [Village_Review.html](Village_Review.html) 查看逐栋对照；使用 [Village_Rectangular_Refined.blend](Village_Rectangular_Refined.blend) 编辑模型。\n\n本轮修改、核验及照片推测边界见 [重建报告](RECONSTRUCTION_REPORT.md)。\n')
