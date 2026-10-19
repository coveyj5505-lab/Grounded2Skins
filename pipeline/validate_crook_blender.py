"""Independent Blender reopen of new crook; original source object remains exact."""
import bpy,json,hashlib,sys
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]);r=json.loads((root/'crook-authoring-report.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(root/'BoPeep-Crook-Accessory-Source.blend'))
o=bpy.data.objects['Crook_Preserved_NOT_EXPORTED'];m=o.data
sig=hashlib.sha256(repr(([tuple(v.co) for v in m.vertices],[tuple(f.vertices) for f in m.polygons],[[tuple(v.uv) for v in layer.data] for layer in m.uv_layers],[list(row) for row in o.matrix_world])).encode()).hexdigest();assert sig==r['original_crook_signature']
mesh=bpy.data.objects['BoPeep_Skinned'];mesh.data.calc_loop_triangles();assert len(mesh.data.vertices)==391 and len(mesh.data.loop_triangles)==590
assert len(mesh.vertex_groups)==192 and len(bpy.data.objects['Grounded2_Willow_192'].data.bones)==192
assert all(len(v.groups)==1 and v.groups[0].group==0 and v.groups[0].weight==1 for v in mesh.data.vertices)
assert [tuple(v.uv) for v in mesh.data.uv_layers.active.data]==[tuple(v.uv) for v in m.uv_layers.active.data]
for i in range(3):
 assert abs(min(v.co[i] for v in mesh.data.vertices)-r['bounds_local_m']['min'][i])<1e-6
 assert abs(max(v.co[i] for v in mesh.data.vertices)-r['bounds_local_m']['max'][i])<1e-6
assert all(bpy.data.images[i['name']].packed_file for i in r['textures'])
r['independent_blender_reopen']='PASS: original signature,391vertices/590triangles,192bone table,root0weights,UVexact,bounds,packedtextures';(root/'crook-authoring-report.json').write_text(json.dumps(r,indent=2)+'\n');print('CROOK_BLENDER_REOPEN_PASS')
