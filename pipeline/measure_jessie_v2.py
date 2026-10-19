"""Independent V1/V2 source-space and posed clothing attachment comparison."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('report',type=Path);a=p.parse_args();r=a.stage;assert not a.report.exists()
x=np.load(r/'audit/park_jessie_ob0_L0.npz');source=x['source'];labels=x['component'];pairs=[]
for chaps,denim in [(27,1201),(1631,3318)]:
 ci=np.flatnonzero(labels==chaps);di=np.flatnonzero(labels==denim);distance,nearest=cKDTree(source[ci]).query(source[di]);select=distance<.025;pairs.extend(zip(di[select].tolist(),ci[nearest[select]].tolist()))
assert len(pairs)>10;pairs=np.asarray(pairs)
records=[]
for pose in ['rest-front','standing','sitting','running']:
 v1=np.load(r/'controlled-v1'/(pose+'.npz'));v2=np.load(r/'controlled-v4'/(pose+'.npz'));assert np.allclose(v1['bone_world'],v2['bone_world'],atol=2e-5)
 d1=np.linalg.norm(v1['positions'][pairs[:,0]]-v1['positions'][pairs[:,1]],axis=1);d2=np.linalg.norm(v2['positions'][pairs[:,0]]-v2['positions'][pairs[:,1]],axis=1)
 records.append({'pose':pose,'paired_vertices':len(pairs),'V1_max_gap_m':float(d1.max()),'V2_max_gap_m':float(d2.max()),'V1_mean_gap_m':float(d1.mean()),'V2_mean_gap_m':float(d2.mean())})
expected=np.load(r/'fit-v4/expected.npz');skin=np.load(r/'fit-v4/skin.npz');old=np.load(r.parent/'jessie-stage/gameplay-v1/expected.npz');mask=expected['accepted_head'];assert np.array_equal(expected['positions'][mask],old['positions'].astype('f4')[mask]);assert np.array_equal(expected['loop_uv'],old['loop_uv'].astype('f4'))
ref=json.loads((r.parent/'jessie-stage/hoops-stock-normalized/rig-reference.json').read_text())['meshes'][0]['bones'];leg={b['index'] for b in ref if any(n in b['name'] for n in ['UpperLeg','LowerLeg','Foot_JNT','Toes_JNT'])};arms=np.isin(expected['region'],['arm','hand']);assert not np.any(np.isin(skin['joints'][arms],list(leg))&(skin['weights'][arms]>0))
result={'same_native_world_pose_for_V1_V2':True,'cloth_pair_selection':'Original source nearest vertices between denim and chaps components, within2.5cm; not a complete collision test','clothing_pairs':records,'accepted_head_vertices_exact':int(mask.sum()),'atlas_UVs_exactly_V1':True,'arms_and_hands_have_zero_leg_influences':True,'runtime':'NOT TESTED; synthetic posed comparison only'};a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
