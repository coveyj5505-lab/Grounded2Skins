import bpy,json,numpy as np
from pathlib import Path
out=Path('/workspace/mod-work/skin-fixes-next');reports={}
scenes={'Buzz':('/workspace/mod-work/refinement-next/buzz-arms-v1/Buzz-Arms-Clearance.blend','Buzz_Skinned'),'BoPeep':('/workspace/mod-work/refinement-next/bopeep-cape-v4h/BoPeep-Cape-V4.blend','BoPeep_Skinned'),'Jessie':('/workspace/mod-work/jessie-v2-stage/fit-v4/Jessie-Hoops-V2.blend','Jessie_Skinned'),'Woody':('/workspace/mod-work/anatomy-corrections/woody-author-v1/Woody-Pelvis-Corrected.blend','Woody_Skinned')}
for name,(path,obj) in scenes.items():
 bpy.ops.wm.open_mainfile(filepath=path);o=bpy.data.objects[obj];arm=o.find_armature();P=np.array([v.co[:] for v in o.data.vertices]);groups=[g.name for g in o.vertex_groups];G=np.zeros((len(P),len(groups)),dtype='f4')
 for v in o.data.vertices:
  for g in v.groups:G[v.index,g.group]=g.weight
 np.savez_compressed(out/(name+'-audit.npz'),positions=P,weights=G,groups=groups)
 reports[name]={'scene':path,'object':obj,'vertices':len(P),'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in arm.data.bones},'mesh_objects':[{'name':x.name,'vertices':len(x.data.vertices)} for x in bpy.data.objects if x.type=='MESH'],'bounds':[P.min(0).tolist(),P.max(0).tolist()]}
(out/'audit.json').write_text(json.dumps(reports,indent=2));print('FOUR_SKIN_AUDIT_DONE')
