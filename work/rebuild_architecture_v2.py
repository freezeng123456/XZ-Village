"""Rebuild the delivered V2 architecture from frozen profiles using Blender's Python."""
from pathlib import Path
import argparse,subprocess,tempfile,shutil,os
p=argparse.ArgumentParser();p.add_argument('--blender',default=shutil.which('blender') or '/Applications/Blender.app/Contents/MacOS/Blender');p.add_argument('--output',type=Path);args=p.parse_args();delivery=Path(__file__).resolve().parent.parent;output=(args.output or delivery/'Rebuilt').resolve();output.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='xz-village-rebuild-') as tmp:
 root=Path(tmp);inputs=root/'work/buildings/v2';inputs.mkdir(parents=True)
 for name in ['inventory.json','profiles.json','final_alignment_audit.json']:shutil.copy2(delivery/name,inputs/name)
 environment=os.environ.copy()
 for name in ['BUILD_IDS','KEEP_EXISTING','ARCHITECTURE_OUT']:environment.pop(name,None)
 cmd=[args.blender,'-b',str(delivery/'Village_Rectangular_Refined.blend'),'-t','6','--python',str(delivery/'source/build_architecture_v2.py')];subprocess.run(cmd,cwd=root,env=environment,check=True)
 generated=root/'outputs/rectangular-photo-refinement';subprocess.run([args.blender,'-b',str(generated/'Village_Rectangular_Candidates.blend'),'-t','4','--python',str(delivery/'source/validate_architecture_v2.py')],cwd=root,check=True)
 import json
 check=json.loads((generated/'validation.json').read_text());assert check['passed'], 'Rebuilt model did not pass geometry validation'
 for path in generated.iterdir():shutil.copy2(path,output/path.name)
print('Rebuilt and structurally validated:',output)
print('Review the rebuilt appearance before using edited profiles as a new visual release.')
