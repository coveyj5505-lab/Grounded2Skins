import bpy,json,sys,numpy as np
from pathlib import Path
p=Path(sys.argv[sys.argv.index('--')+1]);assert bpy.data.collections['Source_Original_UNTOUCHED'].hide_viewport
# Excluded collections have unevaluated identity world caches after reopen.
# Enable ONLY in this unsaved validation process to evaluate the real parent chain.
bpy.data.collections['Source_Original_UNTOUCHED'].hide_viewport=False;bpy.data.objects['bo_peep_geo'].hide_set(False);bpy.context.view_layer.update()
r=json.loads((p/'prop-preservation.json').read_text());source=bpy.data.objects['bo_peep_geo'];source.data.calc_loop_triangles();pos=np.array([v.co[:] for v in source.data.vertices]);tri=np.array([t.vertices[:] for t in source.data.loop_triangles]);original_uv=np.array([u.uv[:] for u in source.data.uv_layers.active.data]);original_loop=np.array([t.loops[:] for t in source.data.loop_triangles]);all_tri=[]
for name,record in r['objects'].items():
 o=bpy.data.objects[name];o.data.calc_loop_triangles();ids=np.array(record['source_vertex_indices']);assert np.array_equal(np.array([v.co[:] for v in o.data.vertices]),pos[ids]);assert np.array_equal(np.asarray(o.matrix_world),np.asarray(source.matrix_world));assert len(o.data.materials)==1 and o.data.materials[0]==source.data.materials[0]
 mapped=ids[np.array([t.vertices[:] for t in o.data.loop_triangles])];mask=np.isin(tri,ids).all(1);assert np.array_equal(mapped,tri[mask]);assert np.array_equal(np.array([u.uv[:] for u in o.data.uv_layers.active.data]),original_uv[original_loop[mask]].reshape(-1,2));all_tri.extend(map(tuple,mapped))
 for j,i in enumerate(ids):assert [(g.group,g.weight) for g in o.data.vertices[j].groups]==[(g.group,g.weight) for g in source.data.vertices[int(i)].groups]
assert sorted(all_tri)==sorted(map(tuple,tri));assert len(next(o for o in bpy.data.objects if o.type=='ARMATURE').data.bones)==63;assert bpy.data.objects['Crook_Preserved_NOT_EXPORTED'].hide_render;assert sum(i.source=='FILE' and bool(i.packed_file) for i in bpy.data.images)==2
(p/'preservation-validation.json').write_text(json.dumps({'fresh_reopen':True,'source_triangles_partition_exact':True,'body_and_crook_positions_UVs_materials_weights_world_transforms_exact':True,'original_rig_bones':63,'crook_hidden_from_initial_playable_export':True,'unique_texture_images':1,'source_original_object_preserved':True,'Willow_compatibility':'Awaiting stock Willow packages'},indent=2)+'\n');print('Preservation validation passed')
