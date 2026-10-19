"""Read-only comparison of native stock/replacement head and hand bindings.
Does not infer runtime camera mode or visibility from offline mesh data.
"""
import json,sys,hashlib
from pathlib import Path
import numpy as np
root=Path(sys.argv[1]);out=Path(sys.argv[2]);assert not out.exists()
models=[
 ('Buzz','cd809abc483f179000000001',root/'stock-max-stage/comparison/stock-reference-skeletons.json',root/'first-person-stage/stock-max-cd809abc483f179000000001',root/'buzz-v2-stage/final-skeletons.json',root/'buzz-v2-stage'),
 ('Woody','b0baaf49556b7e2200000001',root/'woody-stage/pete-stock-normalized/reference-skeletons.json',root/'woody-stage/pete-native/b0baaf49556b7e2200000001',root/'woody-stage/final-check-v1/final-skeletons.json',root/'woody-stage/final-check-v1'),
 ('BoPeep','2ee2517f02d2199900000001',root/'bopeep-stage/willow-stock/reference-skeletons.json',root/'bopeep-stage/willow-body-readback-v3',root/'bopeep-v2-stage/final-check-v1/final-skeletons.json',root/'bopeep-v2-stage/final-check-v1'),
 ('Jessie','911395b71b48cf1a00000001',root/'jessie-stage/hoops-stock-normalized/reference-skeletons.json',root/'jessie-stage/stock-read-911395b71b48cf1a00000001',root/'jessie-v2-stage/final-check-v4/final-skeletons.json',root/'jessie-v2-stage/final-check-v4')]
def inspect(folder,reference):
 m=json.loads((folder/'mesh.json').read_text());sk=next(x for x in json.loads(reference.read_text())['meshes'] if x['chunk_sha256']==m['source_sha256']);bones=sk['bones'];n=m['vertices'];stride=m['influence_stride'];j=np.fromfile(folder/'joints.u16',dtype='<u2').reshape(n,stride);w=np.fromfile(folder/'weights.f32',dtype='<f4').reshape(n,stride);p=np.fromfile(folder/'positions.f32',dtype='<f4').reshape(n,3)
 def subtree(names):
  found={b['index'] for b in bones if b['name'] in names}
  for b in bones:
   if b['parent'] in found:found.add(b['index'])
  return sorted(found)
 masks={k:np.sum(np.where(np.isin(j,subtree(names)),w,0),axis=1)>.5 for k,names in [('head',['head_JNT']),('hands',['l_hand_JNT','r_hand_JNT'])]};head=masks['head'];sections=[]
 for s in m['sections']:
  a,b=s['vertex_start'],s['vertex_start']+s['vertices'];sections.append({'section':s['section'],'material':s['material'],'material_slot_name':m['materials'][s['material']]['name'],'vertices':s['vertices'],'head_vertices':int(head[a:b].sum()),'hand_vertices':int(masks['hands'][a:b].sum())})
 camera=[]
 for b in bones:
  if b['name'].startswith(('FPSpine','FPVcam','FPV_Camera')):camera.append({'index':b['index'],'name':b['name'],'parent':bones[b['parent']]['name'] if b['parent']>=0 else None,'weighted_vertices':int(np.any((j==b['index'])&(w>0),axis=1).sum())})
 return {'source_sha256':m['source_sha256'],'native_bones':len(bones),'vertices':n,'head_vertices':int(head.sum()),'head_bounds_cm':{'min':p[head].min(0).tolist(),'max':p[head].max(0).tolist()} if head.any() else None,'hand_vertices':int(masks['hands'].sum()),'materials':m['materials'],'sections':sections,'first_person_named_bones':camera,'skeleton_name_hierarchy_sha256':hashlib.sha256(json.dumps([(b['name'],b['parent']) for b in bones]).encode()).hexdigest()}
results=[]
for name,cid,stock_ref,stock,modref,modstage in models:
 folder=next(d for d in modstage.glob('final-mesh-readback-*') if d.is_dir() and json.loads((d/'mesh.json').read_text())['source'].endswith(cid));results.append({'character':name,'stock':inspect(stock,stock_ref),'replacement':inspect(folder,modref)})
report={'models':results,'scope':'Independently decoded native vertex bindings/sections; no runtime camera or visibility claim','candidate_failure':'Head and hands must be compared with actual runtime material/section hiding and bone visibility, not assumed camera offsets'};out.write_text(json.dumps(report,indent=2)+'\n')
for r in results:
 print(r['character'])
 for kind in ['stock','replacement']:
  m=r[kind];print(kind,'head',m['head_vertices'],'head sections',[(s['material'],s['material_slot_name'],s['head_vertices']) for s in m['sections'] if s['head_vertices']],'FP weights',[(b['name'],b['weighted_vertices']) for b in m['first_person_named_bones']])
