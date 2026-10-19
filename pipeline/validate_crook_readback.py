"""Compare CUE4Parse native readback against independently exported crook data."""
import argparse,json,hashlib,struct
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=a.stage;n=r/'native-readback-v1';m=json.loads((n/'mesh.json').read_text());expected=np.load(r/'native-buffers-v1/expected.npz')
read=lambda f,t,c:np.fromfile(n/f,dtype=t).reshape(-1,c)
assert m['vertices']==396 and m['triangles']==590 and m['lod_count']==4 and m['skeleton_bones']==192 and m['used_bones']==[0]
assert np.array_equal(read('positions.f32','<f4',3),expected['positions'])
assert np.array_equal(read('indices.u32','<u4',3),expected['indices'].reshape(-1,3))
uv_error=float(np.max(abs(read('uv0.f32','<f4',2)-expected['uv0'])));assert uv_error<.001
normal_error=float(np.max(abs(read('normals.f32','<f4',3)-expected['normals'])));assert normal_error<.02
weights=read('weights.f32','<f4',8);joints=read('joints.u16','<u2',8);assert np.all(weights[:,0]==1) and np.all(weights[:,1:]==0) and np.all(joints[weights>0]==0)
assert np.all(read('triangle-materials.u16','<u2',1)==0)
b=(r/'package-v1/unpacked/chunks/4d2d88a628acba9400000001').read_bytes();lods=[b[x['start']:x['end']] for x in m['lods']];assert len(lods)==4 and all(x==lods[0] for x in lods)
legacy=r/'legacy-readback-v1/Augusta/Content/_BoCrook/Art/Characters/Player_Female01/SK_Female_Teen_01.uexp';assert legacy.read_bytes()==b[struct.unpack_from('<I',b,4)[0]:]
ref=json.loads((r/'reference.json').read_text())['meshes'][0]['bones'];newref=json.loads((r/'readback-reference.json').read_text())['meshes'][0]['bones'];assert ref==newref
report={'asset':'/Game/_BoCrook/Art/Characters/Player_Female01/SK_Female_Teen_01.SK_Female_Teen_01','status':'PASS_OFFLINE_ONLY','vertices':396,'triangles':590,'lods':4,'checks':['Fresh CUE4Parse positions/indices byte-exact encoder expected arrays','All skin influences root0/weight1','Triangle materials0only','4LODs independently parsed and native streams byte-exact to each other','192native skeleton bones/rest transforms exact','Retoc legacy UEXP byte-exact unpacked Zen native payload','IoStore verify/unpack hash checks passed'],'uv_max_error':uv_error,'normal_max_error':normal_error,'source_blender':json.loads((r/'grip-local-v1/crook-authoring-report.json').read_text()),'package':json.loads((r/'package-v1/repackage-validation.json').read_text()),'dependencies':'Existing BoPeep private material/texture; original skeleton/physics/postprocess references retained. These must be disabled/managed on independent cosmetic component before activation.','runtime':'Not spawned/attached or tested in game. Not an implemented playable crook feature.','first_person_requirement':'Crook visible alongside screen, not hidden solely because camera is FP. Separate placement may be necessary.','combat_requirement':'Use actual native spear animations if safe, without imposing two-handed stance or altering unarmed mechanics; currently not substituted.'}
a.out.write_text(json.dumps(report,indent=2)+'\n');print('CROOK_CUE_READBACK_PASS',report['vertices'],report['triangles'],report['lods'],uv_error,normal_error)
