"""Fresh packaged native read-back for root-rigid private accessory sets."""
import argparse,json,hashlib,struct
from pathlib import Path
import numpy as np
from compare_stock_max import names
p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('check',type=Path);p.add_argument('--wings',action='store_true');a=p.parse_args();meta=json.loads((a.check/'final-metadata.json').read_text());skeletons=json.loads((a.check/'final-skeletons.json').read_text())['meshes'];template=Path('/workspace/mod-work/crook-stage');refs=json.loads((template/'reference.json').read_text())['meshes'][0]['bones'];profile=json.loads((template/'native-readback-v1/mesh.json').read_text());original=(template/'package-v1/unpacked/chunks/4d2d88a628acba9400000001').read_bytes();source_imports,_=names(original,struct.unpack_from('<I',original,48)[0]);records=json.loads((a.build/'report.json').read_text())['meshes'];reports=[]
for rec in records:
 cid=rec['chunk'];b=(a.check/'final-unpacked/chunks'/cid).read_bytes();sha=hashlib.sha256(b).hexdigest();m=next(m for m in meta if m['chunk_id']==cid);sk=next(s for s in skeletons if s['chunk_sha256']==sha);assert sk['bones']==refs
 matches=[d for d in a.check.glob('final-mesh-readback-*') if d.is_dir() and json.loads((d/'mesh.json').read_text())['source_sha256']==sha];assert len(matches)==1;d=matches[0];j=json.loads((d/'mesh.json').read_text());folder=a.build/(rec['state']+'-buffers') if a.wings else a.build/rec['kind']/'buffers';e=np.load(folder/'expected.npz');read=lambda f,t,c:np.fromfile(d/f,dtype=t).reshape(-1,c)
 assert j['skeleton_bones']==192 and j['lod_count']==4 and j['used_bones']==[0];assert j['vertices']==rec['vertices'] and j['triangles']==rec['triangles'];assert np.array_equal(read('positions.f32','<f4',3),e['positions']);assert np.array_equal(read('indices.u32','<u4',1).ravel(),e['indices']);assert np.array_equal(read('uv0.f32','<f4',2),e['uv0'].astype('f2').astype('f4'));assert np.max(abs(read('normals.f32','<f4',3)-e['normals']))<.008;assert np.all(read('joints.u16','<u2',8)==0);assert np.array_equal(read('weights.u16','<u2',8),e['quantized_weights']);assert np.all(read('triangle-materials.u16','<u2',1)==0)
 blocks=[b[x['start']:x['end']] for x in j['lods']];assert len(blocks)==4 and all(v==blocks[0] for v in blocks);assert b.count((folder/'static-vertices.bin').read_bytes())==4;assert b[j['material_start']:j['lod_start']]==original[profile['material_start']:profile['lod_start']]
 s=struct.unpack_from('<15I',b);ns,_=names(b,60);package=ns[s[2]&0x3fffffff];objects=[]
 for at in range(s[8],s[9],72):
  ni,num=struct.unpack_from('<II',b,at+16);outer,cls=struct.unpack_from('<QQ',b,at+24)
  if outer==0xffffffffffffffff and ns[ni&0x3fffffff]=='SK_Female_Teen_01':objects.append(package+'.'+ns[ni&0x3fffffff])
 assert objects==[rec['asset']]
 oldmi='/Game/_BoPeep0/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Bop_Apparel01';newmi=oldmi.replace('_BoPeep0','_BzWing0').replace('_Bop_','_Wng_');assert m['imported_packages']==[newmi if a.wings and v==oldmi else v for v in source_imports]
 index=j['materials'][0]['package_index'];obj=struct.unpack_from('<Q',b,s[7]+(-index-1)*8)[0];assert obj>>62==2;v=obj&((1<<62)-1);material=m['imported_packages'][v>>32];assert material==(newmi if a.wings else oldmi)
 import_hash=struct.unpack_from('<Q',b,s[6]+(v&0xffffffff)*8)[0]
 if a.wings:
  target_meta=next(t for t in meta if '/Game/'+t['path'].split('/Content/',1)[1][:-7]==material);target=(a.check/'final-unpacked/chunks'/target_meta['chunk_id']).read_bytes()
 else:
  external=Path('/workspace/mod-work/bopeep-refine-stage/package-v6/unpacked');external_manifest=json.loads((external/'manifest.json').read_text());target_id=next(c for c,path in external_manifest['chunk_paths'].items() if path=='../../../Augusta/Content/'+material.removeprefix('/Game/')+'.uasset');target=(external/'chunks'/target_id).read_bytes()
 target_summary=struct.unpack_from('<15I',target);assert import_hash in [struct.unpack_from('<Q',target,at+56)[0] for at in range(target_summary[8],target_summary[9],72)]

 legacy=a.check/'final-readback-legacy'/m['path'].replace('../../../','');assert legacy.with_suffix('.uexp').read_bytes()==b[s[1]:]
 reports.append({'asset':rec['asset'],'vertices':j['vertices'],'triangles':j['triangles'],'lods':4,'positions_indices_UVs_root_weights_exact':True,'stock_accessory_reference_bones_and_native_properties_preserved':True,'material':material,'material_public_export_hash_verified':True,'actual_package_export_path_verified':True,'legacy_payload_exact':True})
if a.wings:
 # Same verified atlas/MI/texture bytes as the prior read-back; fresh texture
 # probes must independently reproduce all fifty mip payloads.
 old=Path('/workspace/mod-work/wings-stage/final-check-v2');count=0
 for folder in a.check.glob('final-mips-*'):
  for f in folder.glob('mip-*.bin'):assert f.read_bytes()==(old/folder.name/f.name).read_bytes();count+=1
 assert count==50
r={'status':'PASS_OFFLINE_ONLY','meshes':reports,'runtime':'PENDING Windows asset load/attachment; native read-back does not prove runtime loading','verified_texture_mips':50 if a.wings else 'Existing BoPeep textures unchanged'};(a.build/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
