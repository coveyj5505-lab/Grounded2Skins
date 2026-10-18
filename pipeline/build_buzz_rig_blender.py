"""Build the fitted weighted Buzz scene; all paths are new outputs."""
import bpy,json,sys,hashlib,math
from pathlib import Path
import numpy as np

fit_dir,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=False)
d=np.load(fit_dir/'fitted.npz');source=next(o for o in bpy.data.objects if o.type=='MESH');arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
before={b.name:[list(row) for row in b.matrix_local] for b in arm.data.bones};source.data.calc_loop_triangles()
use=d['source_vertices'];lookup=np.full(len(source.data.vertices),-1);lookup[use]=np.arange(len(use))
source_tri=np.asarray([t.vertices[:] for t in source.data.loop_triangles]);source_loops=np.asarray([t.loops[:] for t in source.data.loop_triangles]);keep=d['face_keep'];tri=lookup[source_tri[keep]]
uv=np.asarray([x.uv[:] for x in source.data.uv_layers.active.data],dtype='f4')[source_loops[keep]].reshape(-1,2)
slots=np.asarray([t.material_index for t in source.data.loop_triangles],dtype='i4')[keep]
position=d['positions'][use];mesh=bpy.data.meshes.new('Buzz_Fitted_Skinned_Mesh');mesh.from_pydata(position.tolist(),[],tri.tolist());mesh.update()
obj=bpy.data.objects.new('Buzz_Skinned',mesh);bpy.context.collection.objects.link(obj)
for mat in source.data.materials:mesh.materials.append(mat)
mesh.polygons.foreach_set('material_index',slots);mesh.polygons.foreach_set('use_smooth',np.ones(len(tri),dtype=bool))
layer=mesh.uv_layers.new(name='UVMap');layer.data.foreach_set('uv',uv.ravel())
# Regenerate angle-limited normals across coincident OBJ seam vertices without
# merging topology, UVs, rigid pieces, or skin groups.
_,weld=np.unique(np.round(position,6),axis=0,return_inverse=True)
p=position[tri];cross=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);length=np.linalg.norm(cross,axis=1);assert np.all(length>1e-12)
normal=cross/length[:,None];incident=[[] for _ in range(weld.max()+1)]
for face,vertices in enumerate(weld[tri]):
    for vertex in vertices:incident[vertex].append(face)
custom=[];threshold=math.cos(math.radians(45))
for face,vertices in enumerate(weld[tri]):
    for vertex in vertices:
        candidates=np.asarray(incident[vertex]);select=candidates[(normal[candidates]@normal[face])>=threshold]
        n=cross[select].sum(0);n/=np.linalg.norm(n);custom.append(n.tolist())
mesh.normals_split_custom_set(custom)
groups=[obj.vertex_groups.new(name=b.name) for b in arm.data.bones]
for bone,group in enumerate(groups):
    rows,weight_slots=np.nonzero((d['joints'][use]==bone)&(d['weights'][use]>0));values=d['weights'][use][rows,weight_slots]
    rigid_rows=rows[values==1]
    if len(rigid_rows):group.add(rigid_rows.tolist(),1,'REPLACE')
    for vertex,weight in zip(rows[values!=1],values[values!=1]):group.add([int(vertex)],float(weight),'REPLACE')
arm.name='Grounded2_Armature_230';obj.parent=arm
modifier=obj.modifiers.new('OriginalGrounded2Skeleton','ARMATURE');modifier.object=arm;modifier.use_vertex_groups=True;modifier.use_bone_envelopes=False;modifier.use_deform_preserve_volume=False
obj['source_archive']='buzz-lightyear.zip';obj['fit_status']='Anatomically fitted; controlled-pose verification is separate';obj['game_animation_compatibility']='NOT TESTED'
obj['skin_method']='Constrained Commander101 transfer; rigid armor/wings/boots; digit-specific transfer';obj['facial_animation']='Rigid head, no facial-expression compatibility claim'
if 'wing_components' in d:
    archive=bpy.data.collections.new('Wings_Extended_PRESERVED_NOT_EXPORTED');bpy.context.scene.collection.children.link(archive)
    originals=bpy.data.collections.new('Wings_Original_Source_UNTOUCHED');bpy.context.scene.collection.children.link(originals)
    source_coords=np.asarray([v.co[:] for v in source.data.vertices]);deployment=[]
    for component in d['wing_components']:
        selected=np.flatnonzero(np.all(d['component'][source_tri]==component,axis=1));faces=source_tri[selected];vertices=np.unique(faces)
        mapping={int(v):i for i,v in enumerate(vertices)};wm=bpy.data.meshes.new(f'Wing_{component}_Extended_Mesh')
        wm.from_pydata(d['positions'][vertices].tolist(),[],[[mapping[int(v)] for v in face] for face in faces]);wm.update()
        wo=bpy.data.objects.new(f'Wing_{component}_Extended_Preserved',wm);archive.objects.link(wo)
        for material in source.data.materials:wm.materials.append(material)
        wm.polygons.foreach_set('material_index',np.asarray([source.data.loop_triangles[int(i)].material_index for i in selected]))
        wuv=wm.uv_layers.new(name='UVMap');wuv.data.foreach_set('uv',np.asarray([x.uv[:] for x in source.data.uv_layers.active.data])[source_loops[selected]].ravel())
        wo.vertex_groups.new(name=arm.data.bones[208].name).add(list(range(len(vertices))),1,'REPLACE')
        mod=wo.modifiers.new('RigidChestAttachment','ARMATURE');mod.object=arm;wo.parent=arm
        wo['future_deployment']='Preserved extended panel; hinge/telescoping paths not authored';wo['export_to_initial_game_mesh']=False
        wo.hide_render=True;wo.hide_set(True)
        original=wo.copy();original.data=wm.copy();original.name=f'Wing_{component}_Original_Source';original.modifiers.clear();original.vertex_groups.clear();original.parent=None
        for vertex,co in zip(original.data.vertices,source_coords[vertices]):vertex.co=co
        original.matrix_world=source.matrix_world.copy();originals.objects.link(original);original.hide_render=True;original.hide_set(True)
        original['preservation']='Exact source mesh-local coordinates, UVs, material assignments and source object matrix; no fitting or new weights'
        # Inboard edge is a geometry-based deployment candidate, not an
        # identified engineered hinge. This model has no authored mechanism.
        x=np.abs(source_coords[vertices,0]);inboard=vertices[x<=x.min()+.003]
        candidate=source_coords[inboard].mean(0);fitted_candidate=d['positions'][inboard].mean(0)
        parents={0:12,1:0,12:'backpack/chest',51:'backpack/chest',62:51,72:62}
        role='inner/root panel' if int(component) in (12,51) else 'outer panel' if int(component) in (0,62) else 'tip/detail'
        deployment.append({'component':int(component),'role':role,'candidate_parent':parents[int(component)],'source_local_candidate':candidate.tolist(),'source_object_matrix':[list(row) for row in source.matrix_world],'fitted_extended_candidate':fitted_candidate.tolist(),'basis':'Centroid of vertices within 3mm of minimum absolute source X; inboard panel edge','confidence':'Geometric candidate only; tip/detail pieces may need rigid parenting, not independent hinges'})
    archive.hide_render=True;archive.hide_viewport=True
    originals.hide_render=True;originals.hide_viewport=True
    (out/'wing-deployment-candidates.json').write_text(json.dumps({'units':'Blender meters','deployment_implemented':False,'notes':'No hinge axis, telescoping path, clearances or runtime rig verified. Preserve both source and fitted extended collections.','panels':deployment},indent=2)+'\n')
    obj['wing_state']='Stowed visibility variant; original panels preserved in hidden authoring collection'
bpy.data.objects.remove(source,do_unlink=True)
assert before=={b.name:[list(row) for row in b.matrix_local] for b in arm.data.bones}
assert len(arm.data.bones)==len(obj.vertex_groups)==230
for image in bpy.data.images:
    if image.source=='FILE':assert image.packed_file and image.size[0]>0
bpy.context.view_layer.objects.active=obj;obj.select_set(True);arm.select_set(False)
bpy.context.preferences.filepaths.save_version=0
blend=out/'Buzz-Grounded2-skinned.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
np.savez_compressed(out/'expected.npz',positions=position,triangles=tri,uv=uv,materials=slots,joints=d['joints'][use],weights=d['weights'][use],source_vertices=use,region=d['region'][use],rigid=d['rigid'][use],component=d['component'][use])
report={'vertices':len(position),'triangles':len(tri),'materials':len(mesh.materials),'packed_images':sum(i.source=='FILE' for i in bpy.data.images),'bones':230,'bone_rest_hash':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'reference_rest_matrices_unchanged':True,'normals':'45deg corner smoothing across source seams; no topology merge','blender_file':str(blend),'game_test':'NOT RUN'}
(out/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
