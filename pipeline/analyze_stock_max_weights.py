"""Compare weighted rest frames and inventory physics imports; never edits assets."""
import argparse,json,sys,struct
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

from compare_reference_skeletons import compare
p=argparse.ArgumentParser();p.add_argument('stock_folder',type=Path);p.add_argument('reference',type=Path);p.add_argument('buzz_npz',type=Path);p.add_argument('new_output',type=Path);args=p.parse_args();assert not args.new_output.exists()
root=args.stock_folder;stock=json.loads((root/'comparison/stock-reference-skeletons.json').read_text())['meshes'];ref=json.loads(args.reference.read_text())['meshes'][0]['bones']
z=np.load(args.buzz_npz);used=sorted(set(z['joints'][z['weights']>0].astype(int).tolist()));print('weighted',len(used))
def worlds(bones):
 out={}
 for b in bones:
  m=np.eye(4);m[:3,:3]=Rotation.from_quat(b['rotation_xyzw']).as_matrix()@np.diag(b['scale_xyz']);m[:3,3]=b['translation_cm'];out[b['name']]=m if b['parent']<0 else out[bones[b['parent']]['name']]@m
 return out
rworld=worlds(ref);sworld=worlds(stock[0]['bones']);byname={b['name']:b for b in stock[0]['bones']};rows=[]
for i in used:
 b=ref[i];name=b['name']
 if name not in sworld: rows.append({'bone':name,'missing_from_stock_mesh':True});continue
 r,s=rworld[name],sworld[name];rn=r[:3,:3]/np.linalg.norm(r[:3,:3],axis=0);sn=s[:3,:3]/np.linalg.norm(s[:3,:3],axis=0)
 rows.append({'bone':name,'Commander_index':i,'stock_index':byname[name]['index'],'world_translation_error_cm':float(np.linalg.norm(r[:3,3]-s[:3,3])),'world_rotation_error_deg':float(np.degrees(Rotation.from_matrix(rn.T@sn).magnitude())),'vertices_with_influence':int(np.any((z['joints']==i)&(z['weights']>0),axis=1).sum())})
print(json.dumps([r for r in rows if r.get('missing_from_stock_mesh') or r.get('world_translation_error_cm',0)>.01 or r.get('world_rotation_error_deg',0)>1],indent=2))
links=[]
for entry in json.load(open(root/'extraction-report.json'))['chunks']:
 if not entry['path'].endswith(('SK_Male_Teen_01.uasset','SK_Male_Teen_01_w_BackPack.uasset')):continue
 raw=(root/'chunks'/entry['id']).read_bytes();su=struct.unpack_from('<15I',raw);asset=next(a for a in json.load(open(root/'comparison/comparison.json'))['assets'] if a['chunk']==entry['id']);targets=[]
 for k in range((su[8]-su[7])//8):
  enc=struct.unpack_from('<Q',raw,su[7]+k*8)[0]
  if enc>>62!=2:continue
  pkg=(enc&((1<<62)-1))>>32
  if pkg<len(asset['imported_packages']) and 'PhysicsAsset' in asset['imported_packages'][pkg]:
   start=su[1];stop=next(s['offset'] for s in stock if s['chunk_sha256']==entry['sha256']);pat=struct.pack('<i',-k-1);targets.append({'import_table_index':k,'target_package':asset['imported_packages'][pkg],'serialized_reference_candidate_offsets':[j for j in range(start,stop-3) if raw[j:j+4]==pat]})
 links.append({'mesh':entry['path'],'physics_links':targets})
print('physics',links)
report={'stock_mesh_body_backpack_bones_exact':stock[0]['bones']==stock[2]['bones'],'stock_mesh_vs_stock_USkeleton':compare(stock[0]['bones'],stock[1]['bones']),'Buzz_weighted_bones_world_comparison':rows,'stock_mesh_physics_imports':links,'warning':'World rest transforms are diagnostic only. This is not animation playback, retarget-setting deserialization or runtime validation.'}
args.new_output.write_text(json.dumps(report,indent=2)+'\n')
