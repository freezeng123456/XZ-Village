"""Extend the checked-in landmark scene with observed multi-view surfaces.

Run using Blender -b outputs/Village_Realistic_Target.blend --python ...
No legacy asset is overwritten. New observations and inferred site elements
have separate collections and provenance metadata.
"""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector

ROOT=Path.cwd();PACKAGE=ROOT/'work/aerial/package';OUT=ROOT/'outputs/aerial-continuation';OUT.mkdir(exist_ok=True)
s=bpy.context.scene
bpy.context.preferences.filepaths.save_version=0
s.view_layers[0].material_override=None
legacy=bpy.data.collections['04 Neighbourhood | video-projected context, approximate depth']
legacy.hide_render=True;legacy.hide_viewport=True
legacy['status']='Legacy single-view projected context retained for comparison; disabled in new scene.'
def collection(name):
    c=bpy.data.collections.new(name);s.collection.children.link(c);return c
surfaces=collection('06 OBSERVED | multi-view supported surface patches')
inferred=collection('07 TRACED | pond and bridge; heights estimated')
capture=collection('08 CAMERAS | recovered aerial poses and path')
audit=collection('09 EVIDENCE | supported point cloud; hidden by default')
audit.hide_render=True;audit.hide_viewport=True
structured=collection('10 STRUCTURAL DRAFT | roof-constrained neighbour volumes')

def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.8
    return m
photo=bpy.data.materials.new('Observed surface colour | baked source illumination');photo.use_nodes=True
n=photo.node_tree.nodes;n.clear();attr=n.new('ShaderNodeVertexColor');attr.layer_name='SourceColor'
em=n.new('ShaderNodeEmission');out=n.new('ShaderNodeOutputMaterial');photo.node_tree.links.new(attr.outputs['Color'],em.inputs['Color']);photo.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
def mesh(name,verts,faces,coll,mat=None,colors=None):
    me=bpy.data.meshes.new(name)
    # Bulk arrays avoid per-face Python overhead for the reconstructed surfaces.
    verts=np.asarray(verts,np.float32);faces=np.asarray(faces,np.int32)
    me.vertices.add(len(verts));me.vertices.foreach_set('co',verts.ravel())
    if len(faces):
        width=faces.shape[1];me.loops.add(faces.size);me.polygons.add(len(faces))
        me.loops.foreach_set('vertex_index',faces.ravel());me.polygons.foreach_set('loop_start',np.arange(len(faces),dtype=np.int32)*width)
        me.polygons.foreach_set('loop_total',np.full(len(faces),width,np.int32))
    me.update()
    if colors is not None:
        rgba=np.ones((len(verts),4),np.float32);rgb=np.asarray(colors,np.float32)/255
        # Source JPEG is sRGB; Blender colour attributes contain linear values.
        rgba[:,:3]=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
        ca=me.color_attributes.new(name='SourceColor',type='FLOAT_COLOR',domain='POINT');ca.data.foreach_set('color',rgba.ravel())
    ob=bpy.data.objects.new(name,me);coll.objects.link(ob)
    if mat:me.materials.append(mat)
    return ob

summary=json.loads((PACKAGE/'summary.json').read_text())
for part in summary['parts']:
    p=PACKAGE/(part['name']+'.npz')
    if not p.exists():continue
    z=np.load(p);ob=mesh(part['name']+' | observed',z['xyz'],z['faces'],surfaces,photo,z['rgb'])
    ob['evidence']='Two-view triangulation; forward/backward, reprojection and ray-angle gates; supported by a disjoint second pair.'
    ob['source_frames']=part['name'];ob['precision']='Nominal scale only. Partial surfaces, with gaps retained.'
    print('SURFACE',part['name'],len(z['faces']),flush=True)
z=np.load(PACKAGE/'cloud.npz');ob=mesh('Observed points | cross-pair supported',z['xyz'],[],audit,photo,z['rgb'])
ob['evidence']='Same observed support as surface patches, before meshing. Isolated vertices are intentional.'

# Roof-constrained editable proxies fill simple building envelopes separately
# from the observed patches. Photo appearance is valid near the reference view.
import bmesh
sourcephoto=bpy.data.materials.new('Neighbour draft | 48s appearance, view-dependent');sourcephoto.use_nodes=True
n=sourcephoto.node_tree.nodes;n.clear();tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'work/aerial/sfm/images/f048.00.jpg'));tex.image.pack()
em=n.new('ShaderNodeEmission');output=n.new('ShaderNodeOutputMaterial');sourcephoto.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);sourcephoto.node_tree.links.new(em.outputs[0],output.inputs['Surface'])
neutral=material('Unobserved neighbour face | estimated plaster',(.57,.56,.51))
row=next(p for p in json.loads((PACKAGE/'cameras.json').read_text()) if p['time_seconds']==48)
M=np.array(row['matrix']);campos=M[:3,3];camrot=M[:3,:3]
for item in json.loads((PACKAGE/'neighbour_roofs.json').read_text()):
    roof=np.array(item['roof_vertices']);base=roof.copy();base[:,2]=.05;verts=np.concatenate((base,roof));count=len(roof)
    faces=[]
    # Triangles handle non-quadrilateral outlines with the same mesh utility.
    from mathutils.geometry import tessellate_polygon
    vectors=[Vector(p) for p in roof]
    for tri in tessellate_polygon([vectors]):
        idx=[int(v) if isinstance(v,int) else min(range(count),key=lambda i:(vectors[i]-v).length) for v in tri]
        faces.append([j+count for j in idx])
    for i in range(count):
        j=(i+1)%count;faces.extend([[i,j,j+count],[i,j+count,i+count]])
    ob=mesh(item['name']+' | structural draft',verts,faces,structured,sourcephoto)
    ob.data.materials.append(neutral)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=8,use_grid_fill=True);bm.to_mesh(ob.data);bm.free()
    uv=ob.data.uv_layers.new(name='48s reference projection')
    for loop in ob.data.loops:
        v=np.array(ob.data.vertices[loop.vertex_index].co);pc=camrot.T@(v-campos);nx,ny=pc[0]/(-pc[2]),-pc[1]/(-pc[2]);dist=1+.0334807*(nx*nx+ny*ny)
        uv.data[loop.index].uv=((row['focal_pixels']*nx*dist+800)/1600,1-(row['focal_pixels']*ny*dist+450)/900)
    for face in ob.data.polygons:
        if Vector(campos-face.center).dot(face.normal)<=0:face.material_index=1
    for key,value in item.items():
        if isinstance(value,(str,int,float)):ob[key]=value
    ob['appearance_limit']='48s projection on visible faces; unobserved faces plain. Caps simplify pitched roofs. Disable collection 10 for observation-only inspection.'

water=material('Estimated pond water',(.07,.11,.095));red=material('Traced red pond railing',(.35,.035,.025));stone=material('Estimated concrete bridge',(.42,.43,.4))
water.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.3
def line(name,pts,r,mat,coll=inferred):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for a,p in zip(sp.points,pts):a.co=(*p,1)
    ob=bpy.data.objects.new(name,cu);coll.objects.link(ob);cu.materials.append(mat);return ob
for item in json.loads((PACKAGE/'site_traces.json').read_text()):
    pts=np.array(item['vertices']);name=item['name'];kind=item['kind']
    if kind=='water':
        # Triangulate the traced concave boundary explicitly.
        from mathutils.geometry import tessellate_polygon
        vectors=[Vector(p) for p in pts];tri=tessellate_polygon([vectors]);faces=[]
        for t in tri:faces.append([int(v) if isinstance(v,int) else min(range(len(vectors)),key=lambda i:(vectors[i]-v).length) for v in t])
        ob=mesh(name,pts,faces,inferred,water)
    elif kind=='rail':
        ob=line(name,pts+np.array([0,0,1.05]),.045,red)
        line(name+' lower',pts+np.array([0,0,.45]),.032,red)
        for a,b in zip(pts[:-1],pts[1:]):
            length=np.linalg.norm(b-a)
            for fraction in np.linspace(0,1,max(2,math.ceil(length/1.5))):
                p=a+(b-a)*fraction;line('Estimated railing post',[p,p+[0,0,1.12]],.04,red)
    else:
        a,b=pts;direction=(b-a)/np.linalg.norm(b-a);offset=np.cross(direction,[0,0,1])*1.15
        ob=mesh(name,[a-offset,a+offset,b+offset,b-offset],[[0,1,2],[0,2,3]],inferred,stone)
        for off in [-offset,offset]:
            line('Bridge estimated red railing',[a+off+[0,0,1],b+off+[0,0,1]],.045,red)
    ob['evidence']=item['evidence'];ob['source_time_seconds']=48

poses=json.loads((PACKAGE/'cameras.json').read_text());by_time={}
for row in poses:
    t=row['time_seconds'];name=f'Video {t:06.2f}s | recovered'
    ca=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,ca);capture.objects.link(ob)
    ob.matrix_world=Matrix(row['matrix']);ca.lens=row['focal_pixels']*36/row['width'];ca.sensor_width=36;ca.sensor_fit='HORIZONTAL'
    ca.clip_end=2000;ca.display_size=1.8;ob['evidence']='COLMAP recovered pose; nominal roof-width scale; standard pinhole view uses undistorted source.'
    by_time[t]=ob
pathmat=material('Recovered flight path cyan',(.03,.5,.7))
trajectory=line('Recovered flight path',[np.array(p['matrix'])[:3,3] for p in poses],.12,pathmat,capture);trajectory.hide_render=True
def camera(name,pos,target,lens=45,ortho=None):
    ca=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,ca);capture.objects.link(ob);ob.location=pos
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();ca.lens=lens;ca.clip_end=2000
    if ortho:ca.type='ORTHO';ca.ortho_scale=ortho
    return ob
overview=camera('Review | village oblique',(-185,-215,235),(-55,60,0),43)
top=camera('Review | plan view',(-50,55,370),(-50,55,0),ortho=420)
pond=camera('Review | pond geometry',(100,-20,105),(-7,93,0),48)

for c in bpy.data.collections:
    if c.name.startswith(('01 TARGET','02 TARGET','03 TARGET')):
        c['status']='Existing editable landmark retained. Hidden and unobserved details remain approximations from the baseline.'
s['Reconstruction_status']='Partial multi-view surface reconstruction; existing editable landmark retained. Not a full watertight or survey-grade village.'
s['Observed_surface_triangles']=summary['triangles'];s['Supported_cloud_points']=summary['cloud_points']
s['Source_video_sha256']=json.loads((ROOT/'work/aerial/reference/source_manifest.json').read_text())['sha256']
s['Scale']='Nominal 7.5m target roof width inherited from prior visual estimate; no surveyed scale.'
s['Disconnected_return_segment']='14 return frames form a separate model, excluded from this aligned scene.'
text=bpy.data.texts.new('READ ME | evidence and limits');text.write(json.dumps(summary,ensure_ascii=False,indent=2))
text=bpy.data.texts.new('ALIGNMENT | nominal scale');text.write((ROOT/'work/aerial/alignment.json').read_text())
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.use_denoising=True
s.render.resolution_x=1600;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.world.use_nodes=True;wn=s.world.node_tree.nodes;wn.clear()
ambient=wn.new('ShaderNodeBackground');ambient.inputs[0].default_value=(.72,.77,.82,1);ambient.inputs[1].default_value=.7
backdrop=wn.new('ShaderNodeBackground');backdrop.inputs[0].default_value=(.055,.069,.077,1);backdrop.inputs[1].default_value=.6
lightpath=wn.new('ShaderNodeLightPath');mix=wn.new('ShaderNodeMixShader');wo=wn.new('ShaderNodeOutputWorld')
wl=s.world.node_tree.links;wl.new(lightpath.outputs['Is Camera Ray'],mix.inputs[0]);wl.new(ambient.outputs[0],mix.inputs[1]);wl.new(backdrop.outputs[0],mix.inputs[2]);wl.new(mix.outputs[0],wo.inputs['Surface'])
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
s.camera=overview
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_end=2000
            area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='VERTEX'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Village_Aerial_Continuation.blend'),compress=True)
for name,cam,w,h in [('Village_Structural_Oblique',overview,1600,1000),('Village_Structural_48s',by_time[48],1600,900)]:
    s.camera=cam;s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
structured.hide_render=True
for name,cam,w,h in [('Village_Observed_Oblique',overview,1600,1000),('Village_Observed_48s',by_time[48],1600,900),('Village_Observed_Plan',top,1600,1200)]:
    s.camera=cam;s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
clay=material('Review clay',(.48,.51,.53));s.view_layers[0].material_override=clay;s.camera=pond;s.render.resolution_x=1600;s.render.resolution_y=1000
s.render.filepath=str(OUT/'Village_Geometry_Review.png');bpy.ops.render.render(write_still=True)
print('CONTINUATION_COMPLETE',flush=True)
