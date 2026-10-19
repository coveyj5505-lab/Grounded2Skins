"""Fresh-reopen fingerprints for source Jessie geometry, UVs, rig and weights."""
import bpy,json,sys,hashlib
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1]);assert not out.exists()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
meshes=[]
for o in sorted((x for x in bpy.data.objects if x.type=='MESH'),key=lambda x:x.name):
 o.data.calc_loop_triangles()
 record={'name':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'positions_hash':digest([list(v.co) for v in o.data.vertices]),'UV_hash':digest([[list(v.uv) for v in layer.data] for layer in o.data.uv_layers]),'triangles_hash':digest([list(t.vertices) for t in o.data.loop_triangles]),'skin_hash':digest([[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices]),'matrix_world':[[x for x in row] for row in o.matrix_world]}
 for v in o.data.vertices:assert len(v.groups)>0 and abs(sum(g.weight for g in v.groups)-1)<1e-4
 meshes.append(record)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');bones=[{'name':b.name,'parent':b.parent.name if b.parent else None,'matrix':[[x for x in row] for row in b.matrix_local]} for b in arm.data.bones]
assert len(bones)==163
report={'meshes':meshes,'bones':163,'bone_rest_hash':digest(bones),'all_vertices_weighted_normalized':True,'packed_images':[i.name for i in bpy.data.images if i.source=='FILE' and i.packed_file]};out.write_text(json.dumps(report,indent=2)+'\n');print('Source fingerprint passed:',sum(m['vertices'] for m in meshes),'vertices,',len(bones),'bones')
