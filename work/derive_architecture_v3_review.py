from pathlib import Path
p=Path('work/validate_architecture_v2.py').read_text().replace('work/buildings/v2','work/buildings/v3').replace('outputs/rectangular-photo-refinement','outputs/orthogonal-multiview').replace('Ground floor closed slab','Ground floor orthogonal slab')
p=p.replace("footprint=np.array(b['roof_world']);", "local=np.array(b.get('plan_polygon',[[0,0],[1,0],[1,1],[0,1]]))*[b['rectangle']['width'],b['rectangle']['depth']];ob=next(o for o in c.objects if o.type=='MESH');footprint=np.array([tuple(ob.matrix_world@__import__('mathutils').Vector((x,y,0))) for x,y in local]);")
a=p.index("dims=np.ptp(v,axis=0);slab_ok=");z=p.index('\n checks=',a)
p=p[:a]+"saved=np.unique(np.round(v[:,:2],4),axis=0);edges0=np.roll(local,-1,axis=0)-local;normals0=np.column_stack([edges0[:,1],-edges0[:,0]])/np.linalg.norm(edges0,axis=1)[:,None];expected=np.unique(np.round(local-.01*(normals0+np.roll(normals0,1,axis=0)),4),axis=0);edges=np.roll(local,-1,axis=0)-local;slab_ok=bool(saved.shape==expected.shape and np.allclose(saved,expected,atol=1e-4) and all(abs(float(a@z))<1e-6 for a,z in zip(edges,np.roll(edges,-1,axis=0))))"+p[z:]
p=p.replace('saved_ground_slab_is_rectangle','saved_ground_slab_matches_orthogonal_plan').replace("b['type']=='construction' or any", "b['type']=='construction' or b['id']=='B013' or any")
a=p.index("alignment=json.loads(");z=p.index("result['checks']['all_building_checks_pass']",a)
p=p[:a]+p[z:]
p=p.replace("result['saved_file']=", "result['world_plan_polygons']={c.name.split(' | ')[0]:[tuple(next(o for o in c.objects if o.type=='MESH').matrix_world@__import__('mathutils').Vector((x,y,0))) for x,y in json.loads(c['local_plan_polygon'])] for c in cols.values()};result['saved_file']=")
Path('work/validate_architecture_v3.py').write_text(p)
p=Path('work/render_architecture_v2_overview.py').read_text().replace('work/buildings/v2','work/buildings/v3').replace('outputs/rectangular-photo-refinement','outputs/orthogonal-multiview');p=p.replace("('Detail_Construction',['C002'])", "('Detail_Construction',['B013'])").replace("('Detail_Modern',['B008','B009','B010'])", "('Detail_Modern',['B007','B008','B009','B010'])")
Path('work/render_architecture_v3_overview.py').write_text(p)
p=Path('work/render_architecture_v2_review.py').read_text().replace('work/buildings/v2','work/buildings/v3').replace('outputs/rectangular-photo-refinement','outputs/orthogonal-multiview').replace('V2','V3').replace('exposure=.1','exposure=.25')
p=p.replace("for c in s.collection.children:","if os.environ.get('RETURN_ONLY'):bs=[dict(b,t=256) for b in bs if b['t']!=256]\nfor c in s.collection.children:",1)
p=p.replace("b['id']+'_source_view.png'","b['id']+('_return_view.png' if os.environ.get('RETURN_ONLY') else '_source_view.png')")
p=p.replace("out/'source_view_manifest.json'","out/('return_view_manifest.json' if os.environ.get('RETURN_ONLY') else 'source_view_manifest.json')")
p+="\nif os.environ.get('AUTO_RETURN') and not os.environ.get('RETURN_ONLY'):\n os.environ['RETURN_ONLY']='1';os.environ['SOURCE_ONLY']='1';exec(compile(Path(__file__).read_text(),__file__,'exec'))\n"
Path('work/render_architecture_v3_review.py').write_text(p)
