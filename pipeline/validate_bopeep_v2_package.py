"""Prove Bo Peep V2 changes only its two body chunks and preserves releases."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1];old=root.parent/'bopeep-stage'
before=old/'package-v3/unpacked/chunks';after=root/'final-check-v1/final-unpacked/chunks'
a={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in before.iterdir() if not p.name.endswith('00000006')};b={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in after.iterdir() if not p.name.endswith('00000006')};assert a.keys()==b.keys()
changed=[cid for cid in a if a[cid]!=b[cid]];body=[p['chunk'] for p in json.loads((old/'stock-native-profiles.json').read_text()) if '/Hair/' not in p['path']];assert sorted(changed)==sorted(body) and len(changed)==2
baselines={'Buzz-Lightyear-V2-Proportions-Test.zip':'42b0c50091bc7a5fb97a37ff91ff06da9c0f3f5eac5dd04fba241520aa837250','BoPeep-Willow-First-Test.zip':'1839b9e660a274f75a929a5387bd3daa7bba75dbceff92224b6e66fa578b5422','Jessie-Hoops-V2-Test.zip':'c96f405ca6a5424b9c9b74ed78bcbf5679f125e8ab43160f56262a41c813c283','Woody-Pete-First-Test.zip':'770661afc75557c03302becc2bf97043d616a88711ed1f58b233e013182e2aca'}
for name,sha in baselines.items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==sha
prior=np.load(old/'geometry-v3/BoPeep-geometry-SKINNED.npz');current=np.load(root/'geometry-v3/BoPeep-geometry-SKINNED.npz')
assert np.array_equal(prior['source_vertices'][prior['indices']],current['source_vertices'][current['indices']])
assert np.array_equal(prior['uv0'][prior['indices']],current['uv0'][current['indices']])
source=np.load(root/'fit-v1/expected.npz');unchanged=source['regions']=='unchanged';lookup={int(v):i for i,v in enumerate(prior['source_vertices'])}
for i,vid in enumerate(current['source_vertices']):
 if not unchanged[vid]:continue
 j=lookup[int(vid)];assert np.array_equal(current['positions'][i],prior['positions'][j]);assert np.array_equal(current['joints'][i],prior['joints'][j]);assert np.array_equal(current['weights'][i],prior['weights'][j])
frames=root/'frames-v1';expected=np.load(root/'buffers-v1/expected.npz');errors={}
for key,file in [('normals','normals.f32'),('tangents','tangents.f32')]:
 decoded=np.fromfile(frames/file,dtype='<f4').reshape(-1,3);errors[key+'_max_component_error']=float(np.max(abs(decoded-expected[key])));assert errors[key+'_max_component_error']<.0041
assert np.array_equal(np.fromfile(frames/'signs.f32',dtype='<f4'),expected['signs'])
report={'changed_body_chunks':changed,'unchanged_private_material_texture_bulk_and_hair_chunks':len(a)-2,'all_triangle_source_vertex_IDs_and_UVs_exact_V1':True,'unchanged_body_regions_encoded_positions_joints_weights_exact':True,'other_release_sha256_unchanged':baselines,'normal_tangent_readback':errors,'tangent_handedness_exact':True,'runtime':'NOT TESTED'}
(root/'baseline-preservation-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
