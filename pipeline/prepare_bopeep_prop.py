"""Separate the source rig's e_stick prop; preserve source object and transforms."""
import bpy,json,sys,hashlib
from pathlib import Path
import numpy as np
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=False)
source=next(o for o in bpy.data.objects if o.type=='MESH');arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');m=source.data;m.calc_loop_triangles();group=source.vertex_groups.get('e_stick');assert group,'No authored prop group; inspect components instead of guessing'
positions=np.array([v.co[:] for v in m.vertices]);tris=np.array([t.vertices[:] for t in m.loop_triangles]);loops=np.array([t.loops[:] for t in m.loop_triangles]);materials=np.array([t.material_index for t in m.loop_triangles]);uv=np.array([l.uv[:] for l in m.uv_layers.active.data]);normals=np.array([l.normal[:] for l in m.loops]);prop=np.array([sum(g.weight for g in v.groups if g.group==group.index) for v in m.vertices]);mask=prop>0;assert mask.any() and np.allclose(prop[mask],1);inside=mask[tris].all(1);assert not np.any(mask[tris].any(1)&~inside),'Crook shares triangles with body; refusing destructive split'
archive=bpy.data.collections.new('Source_Original_UNTOUCHED');bpy.context.scene.collection.children.link(archive)
for collection in list(source.users_collection):collection.objects.unlink(source)
archive.objects.link(source);archive.hide_render=True;archive.hide_viewport=True;source.hide_render=True;source.hide_set(True)
created={}
for label,selected in [('BoPeep_Body',~inside),('Crook_Preserved_NOT_EXPORTED',inside)]:
 ids=np.unique(tris[selected]);mapping=np.full(len(positions),-1);mapping[ids]=np.arange(len(ids));mesh=bpy.data.meshes.new(label+'_Mesh');mesh.from_pydata(positions[ids].tolist(),[],mapping[tris[selected]].tolist());mesh.update()
 obj=source.copy();obj.name=label;obj.data=mesh;obj.modifiers.clear();obj.vertex_groups.clear();bpy.context.scene.collection.objects.link(obj);obj.hide_render=False;obj.hide_set(False)
 for material in source.data.materials:mesh.materials.append(material)
 mesh.polygons.foreach_set('material_index',materials[selected]);mesh.polygons.foreach_set('use_smooth',np.ones(selected.sum(),dtype=bool));layer=mesh.uv_layers.new(name=m.uv_layers.active.name);layer.data.foreach_set('uv',uv[loops[selected]].ravel());mesh.normals_split_custom_set(normals[loops[selected]].reshape(-1,3).tolist())
 groups=[obj.vertex_groups.new(name=g.name) for g in source.vertex_groups]
 for j,old in enumerate(ids):
  for g in m.vertices[int(old)].groups:groups[g.group].add([j],g.weight,'REPLACE')
 mod=obj.modifiers.new('OriginalSourceRig','ARMATURE');mod.object=arm;obj['initial_playable_export']=label=='BoPeep_Body'
 if label.startswith('Crook'):obj.hide_render=True;obj.hide_set(True)
 created[label]={'vertices':len(ids),'triangles':int(selected.sum()),'source_vertex_indices':ids.tolist(),'original_matrix_world':[list(row) for row in source.matrix_world]}
 assert np.array_equal(np.array([v.co[:] for v in mesh.vertices]),positions[ids]);assert np.array_equal(np.asarray(obj.matrix_world),np.asarray(source.matrix_world))
pivot=bpy.data.objects.new('Crook_AuthoredPivot_Candidate',None);bpy.context.scene.collection.objects.link(pivot);pivot.location=arm.matrix_world@arm.data.bones['e_stick'].head_local;pivot.empty_display_size=.05;pivot['purpose']='Authored source e_stick bone-head reference; native Willow hand attachment not yet verified'
report={'separation':'Complete source-rig e_stick weights; no mixed body/crook triangles','objects':created,'crook_excluded_from_initial_playable_mesh':True,'source_original_retained_hidden':True,'source_geometry_UVs_materials_weights_transforms_preserved':True,'crook_pivot_world':list(pivot.location),'future_hand_attachment':'Resolve Willow hand bone after stock extraction; no input/gliding/umbrella feature implemented','native_Willow_rig':'Not yet supplied; source63-bone rig is not assumed animation-compatible'}
(out/'prop-preservation.json').write_text(json.dumps(report,indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'BoPeep-source-body-and-crook.blend'),compress=True);print(json.dumps({k:v for k,v in report.items() if k!='objects'}));print({k:{'vertices':v['vertices'],'triangles':v['triangles']} for k,v in created.items()})
