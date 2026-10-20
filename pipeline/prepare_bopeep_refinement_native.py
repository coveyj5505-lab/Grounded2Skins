from pathlib import Path
import numpy as np,json,argparse
parser=argparse.ArgumentParser();parser.add_argument('stage',type=Path);parser.add_argument('baseline',type=Path);args=parser.parse_args();root=args.stage;base=args.baseline;geom=dict(np.load(root/'geometry-v5/BoPeep-geometry-SKINNED.npz'));ref=json.loads((base/'reference.json').read_text())['meshes'][0]['bones'];head={b['index'] for b in ref if b['name']=='head_JNT'}
for b in ref:
 if b['parent'] in head:head.add(b['index'])
fraction=np.where(np.isin(geom['joints'],sorted(head)),geom['weights'],0).sum(1);headtri=np.max(fraction[geom['indices']],1)>.25;geom['materials']=np.where(headtri,3,0).astype('u2');profile=json.loads((base/'readback-2ee2517f02d2199900000001/mesh.json').read_text());geom['material_count']=np.array(len(profile['materials']));np.savez_compressed(root/'geometry-fp-v5.npz',**geom)
profiles=[];manifest=json.loads((base/'package/unpacked/manifest.json').read_text())
for cid in ['2ee2517f02d2199900000001','5bf07aadb2b863d000000001']:
 p=json.loads((base/('readback-'+cid)/'mesh.json').read_text());p['chunk']=cid;p['sha256']=p['source_sha256'];p['path']=manifest['chunk_paths'][cid];profiles.append(p)
(root/'writer-profiles.json').write_text(json.dumps(profiles,indent=2)+'\n')
print('HEAD/BODY SECTIONS',int(headtri.sum()),int((~headtri).sum()))
