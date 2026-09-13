from pathlib import Path
import shutil,json,re
P=Path('work/rebuild4/architecture');O=Path('/Users/zenghang/Documents/Codex/2026-09-12/jie/outputs/XZ-Village-Rebuilt-V4');S=O/'rebuild';S.mkdir(exist_ok=True)
files=['rebuild_v4_build_architecture.py','rebuild_v4_roof_details.py','rebuild_v4_distinctive_details.py','rebuild_v4_special_buildings_geometry.py','rebuild_v4_terrace_geometry.py','rebuild_v4_build_environment.py']
for name in files:
 s=(Path('work')/name).read_text().replace("Path('work')",'Path(__file__).resolve().parent')
 if name=='rebuild_v4_build_architecture.py':
  s=s.replace("P=Path('work/rebuild4/architecture').resolve()", "P=Path(__file__).resolve().parent.parent/'data'")
  s=s.replace("'pilot_mesh_input.json'","'architecture_geometry.json'").replace("'pilot_profiles.json'","'architecture_profiles.json'").replace("'pilot_detailed'","'rebuilt_from_data'")
  s=s.replace("if envpath.exists() and os.getenv('V4_GEOMETRY','').startswith('village'):","if envpath.exists():")
 (S/name).write_text(s)
shutil.copy2(P/'village_environment.json',O/'data/village_environment.json')
shutil.copy2(P/'final_roof_source_adjudication.json',O/'evidence/roof_source_adjudication.json')
(S/'HOW_TO_REBUILD.md').write_text('''# 从交付数据重新生成模型

此目录包含最终几何和程序材质的 Blender 生成代码。`../data/` 中的建筑、立面和环境数据已经冻结，生成模型不需要原视频、摄影测量数据库或联网。

在 Blender 的 Scripting 工作区打开 `rebuild_v4_build_architecture.py` 并运行；或在解压后的目录执行：

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 4 --python rebuild/rebuild_v4_build_architecture.py
```

新结果写到 `data/rebuilt_from_data/`，包括 `architecture.blend` 和对应机位图。此命令会清空当前 Blender 场景，因此在空白 Blender 进程运行。它不改写本包的 `Village_Rebuilt_Master.blend`。

本次主文件使用 Blender 5.2.1 生成。脚本使用 Blender 内置 Python 和 NumPy；其他 Blender 版本未测试。

摄影测量的相机质量证据在 `../evidence/`；此脚本仅重建已经整理好的场景，不重新计算原视频相机与稠密点云。
''')
# Include exact viewer sources and third-party license for review, no runtime CDN dependencies.
V=S/'viewer';V.mkdir(exist_ok=True)
for name in ['app.js','template.html','package.json']:
 shutil.copy2(Path('work/rebuild4/viewer')/name,V/name)
shutil.copy2(Path('work/rebuild4/viewer/node_modules/three/LICENSE'),S/'THREE_LICENSE.txt')
print('PACKAGED_BUILD_SOURCES',len(files))
