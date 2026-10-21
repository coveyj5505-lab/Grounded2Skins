import bpy,bmesh,numpy as np,json
from pathlib import Path
r=Path('/tmp/toystory-feedback-v3');reports=[]
def thicken(o):
 o.data.update();P=np.array([v.co[:] for v in o.data.vertices[:391]]);groups={}
 for i,p in enumerate(P):groups.setdefault(tuple(np.round(p,6)),[]).append(i)
 Q=P.copy()
 for ids in groups.values():
  n=np.mean([o.data.vertices[i].normal[:] for i in ids],0);length=np.linalg.norm(n)
  if length<1e-8:continue
  n/=length
  for i in ids:Q[i]=P[i]+.003*n
 Q[:,2]=np.clip(Q[:,2],P[:,2].min(),P[:,2].max())
 for v,q in zip(o.data.vertices[:391],Q):v.co=q
 norms=[]
 for f in o.data.polygons:
  staff=all(i<391 for i in f.vertices)
  for li in f.loop_indices:norms.append((0,0,0) if staff else o.data.loops[li].normal[:])
 o.data.normals_split_custom_set(norms);o.data.update();return {'radial_inflation_m':.003,'staff_vertices':391,'source_height_m':float(np.ptp(P[:,2])),'new_height_m':float(np.ptp(Q[:,2])),'seam_positions_coincident':True}
for name,path in [('CrookHand',r/'CrookHand.blend'),('CrookTP',Path('/workspace/mod-work/refinement-next/crook-grip-v3d/TP-Crook-Grip.blend'))]:
 bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['BoPeep_Skinned'];report=thicken(o);report['view']=name;reports.append(report);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/(name+'.blend')),compress=True)
 if name=='CrookHand':
  bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index>=391],context='VERTS');bm.to_mesh(o.data);bm.free();assert len(o.data.vertices)==391;bpy.ops.wm.save_as_mainfile(filepath=str(r/'CrookBare.blend'),compress=True)
(r/'crook-thickness.json').write_text(json.dumps(reports,indent=2));print('ALL_THREE_CROOK_VIEWS_THICKENED')
