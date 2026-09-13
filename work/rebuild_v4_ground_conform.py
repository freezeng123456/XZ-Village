"""Shared smooth terrain constrained by source roads and building foundation levels.
This is support geometry; surveyed topographic accuracy is not asserted.
"""
from shapely import distance as shape_distance,points as shape_points
initial_zground=zground
original=np.array(d['ground_mesh']['vertices']);terrain_res=1.5;terrain_lo=original[:,:2].min(0);terrain_hi=original[:,:2].max(0);terrain_xs=np.arange(terrain_lo[0],terrain_hi[0]+.1,terrain_res);terrain_ys=np.arange(terrain_lo[1],terrain_hi[1]+.1,terrain_res);tx,ty=np.meshgrid(terrain_xs,terrain_ys);txy=np.column_stack([tx.ravel(),ty.ravel()]);tz=initial_zground(txy).reshape(tx.shape);tz=nd.gaussian_filter(tz,1.2)
# Constrain a small pad at each ground-connected wall. Roof rooms remain above it.
terrain_audit=[]
for b in d['entries']:
 role=b.get('source_role','');roof=b['roof_edge_height'];base=b['base_height'];poly=Polygon(b['footprint_world']);coarse=float(initial_zground(np.array(poly.centroid.coords)[0]));delta=base-coarse
 if role in ['roof_room','roof_fixture_or_room_ambiguous'] or (role in ['shed','canopy'] and delta>2):continue
 mn=np.array(poly.bounds[:2])-7;mx=np.array(poly.bounds[2:])+7;sel=np.flatnonzero(np.all(txy>=mn,axis=1)&np.all(txy<=mx,axis=1))
 if len(sel)==0:continue
 dist=shape_distance(shape_points(txy[sel]),poly);weight=1-np.clip((dist-.8)/5.5,0,1);weight=weight**2*(3-2*weight);flat=tz.ravel();old=flat[sel].copy();target=base-.10;flat[sel]=old*(1-weight)+target*weight
 terrain_audit.append(dict(id=b['id'],base=base,prior_ground=coarse,prior_base_delta=delta,status='inferred terrain support conforming to reconstruction base'))
# Raster interpolation makes roads, fields and terrain query one smooth height field.
terrain_grid=tz.copy()
def zground(xy):
 xy=np.asarray(xy);p=(xy-terrain_lo)/terrain_res;shape=p.shape[:-1];p=p.reshape(-1,2);return nd.map_coordinates(terrain_grid,[p[:,1],p[:,0]],order=1,mode='nearest').reshape(shape)
(P/'ground_contact_constraints.json').write_text(json.dumps(dict(entries=terrain_audit,status='inferred support surfaces, not surveyed terrain')))
print('GROUND CONFORM',len(terrain_audit),'foundation constraints',flush=True)
