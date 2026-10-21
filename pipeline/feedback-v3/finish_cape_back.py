import bpy,bmesh,numpy as np,json
from pathlib import Path
r=Path('/tmp/toystory-feedback-v3');old=Path('/workspace/mod-work/skin-fixes-next');D=np.load(old/'BoPeep/geometry.npz');S=D['source_vertices'];parent=list(range(4972))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for tri in S[D['indices']]:
 if max(tri)>=4972:continue
 root=find(int(tri[0]))
 for i in tri[1:]:parent[find(int(i))]=root
collar={i for i in range(4972) if find(i)==find(1155)};assert len(collar)==227
bpy.ops.wm.open_mainfile(filepath=str(old/'BoPeep-Cape-Continuous-Candidate.blend'));o=bpy.data.objects['BoPeep_Skinned'];saved={}
for f in o.data.polygons:
 for li in f.loop_indices:
  vi=o.data.loops[li].vertex_index;key=(vi,tuple(np.round(o.data.uv_layers.active.data[li].uv,6)));saved[key]=o.data.loops[li].normal[:]
changed=[]
for i in collar:
 v=o.data.vertices[i];t=float(np.clip((v.co.y-.01)/.06,0,1));target=min(v.co.z,1.525)
 if t and target<v.co.z:v.co.z=v.co.z+(target-v.co.z)*t;changed.append(i)
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index>=4972],context='VERTS');uv=bm.loops.layers.uv.active;deform=bm.verts.layers.deform.verify();g=o.vertex_groups['spine3_JNT'].index;tex=json.load(open(old/'collar-patch.json'))['atlas_uv'];rows=[]
# The rear-facing cover follows the outer cape surface, outside its reverse
# lining. Its upper edge is shoulder-height, not the old high neck panel.
for z,width,y in [(1.54,.225,.205),(1.50,.235,.205),(1.44,.25,.200),(1.38,.265,.190),(1.34,.28,.180)]:
 row=[]
 for t in np.linspace(-1,1,17):v=bm.verts.new((float(t*width),float(y+.006*(1-t*t)),z));v[deform][g]=1;row.append(v)
 rows.append(row)
for a,b in zip(rows,rows[1:]):
 for i in range(16):
  f=bm.faces.new([a[i],b[i],b[i+1],a[i+1]]);f.material_index=0;f.smooth=True
  for k,l in enumerate(f.loops):l[uv].uv=(tex[0]+.0002*(k in [2,3]),tex[1]+.0002*(k in [1,2]))
bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if any(v.index<0 for v in f.verts)]);bm.to_mesh(o.data);bm.free();norms=[]
for f in o.data.polygons:
 for li in f.loop_indices:
  vi=o.data.loops[li].vertex_index;key=(vi,tuple(np.round(o.data.uv_layers.active.data[li].uv,6)));norms.append(saved.get(key,(0,0,0)))
o.data.normals_split_custom_set(norms);o.data.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'BoPeep.blend'),compress=True);(r/'cape-final-report.json').write_text(json.dumps({'original_collar_component_vertices':227,'rear_collar_vertices_lowered':len(changed),'rear_collar_limit_m':1.525,'outer_rear_cover_top_z_m':1.54,'old_high_neck_panel_removed':45,'front_lapels_flower':'unmodified','lower_cape_below1.34m':'unmodified','face_body_reference_and_normals':'preserved','purpose':'Cover reverse-lining intersections from outside rather than leaving broken rear faces ahead of an inner patch'},indent=2));print('REAR_CAPE_OUTER_COVER_SAVED')
