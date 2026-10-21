import bpy,json,numpy as np
from pathlib import Path
p=Path('/workspace/mod-work/skin-fixes-next');r={}
bpy.ops.wm.open_mainfile(filepath='/workspace/mod-work/refinement-next/bopeep-cape-v4h/BoPeep-Cape-V4.blend');src=bpy.data.objects['BoPeep_Body'];o=bpy.data.objects['BoPeep_Skinned'];cape=[v.index for v in src.data.vertices if any(src.vertex_groups[g.group].name.startswith('e_cape') for g in v.groups)];P=np.array([src.matrix_world@v.co for v in src.data.vertices]);np.savez_compressed(p/'BoPeep-source.npz',positions=P,cape=cape);r['BoPeep']={'source_vertices':len(P),'cape_bounds':[P[cape].min(0).tolist(),P[cape].max(0).tolist()],'source_armature':src.find_armature().name,'fitted_cape_bounds':[[min(o.data.vertices[i].co[k] for i in cape),max(o.data.vertices[i].co[k] for i in cape)] for k in range(3)]}
bpy.ops.wm.open_mainfile(filepath='/workspace/mod-work/anatomy-corrections/woody-author-v1/Woody-Pelvis-Corrected.blend');r['Woody']={};offset=0
for x in [bpy.data.objects['KH3 Woody V3_mesh'+s] for s in ['', '.001','.002','.003','.004','.005','.006','.007','.008']]:
 P=np.array([x.matrix_world@v.co for v in x.data.vertices]);r['Woody'][x.name]={'start':offset,'end':offset+len(P),'bounds':[P.min(0).tolist(),P.max(0).tolist()],'materials':[m.name for m in x.data.materials],'groups':[g.name for g in x.vertex_groups if any(g.index==q.group for v in x.data.vertices for q in v.groups)]};offset+=len(P)
(p/'detail.json').write_text(json.dumps(r,indent=2));print('DETAIL_DONE')
