"""Independent final packaged stream, material and current-template mip checks."""
import json,hashlib,struct
from pathlib import Path
import numpy as np
from PIL import Image
import texture2ddecoder
r=Path('/workspace/mod-work/ue57-migration');check=r/'jessie-check-v1';raw=check/'final-unpacked/chunks';meta=json.loads((check/'final-metadata.json').read_text());refs=json.loads((check/'final-skeletons.json').read_text())['meshes'];newrefs=json.loads((r/'Hoops/skeletons.json').read_text())['meshes'];rebased=json.loads((r/'jessie-rebase-v4/mesh-validation.json').read_text());build=json.loads((r/'jessie-complete-v1/build-report.json').read_text());meshresults=[]
for item in rebased['meshes']:
 cid=item['chunk'];entry=next(m for m in meta if m['chunk_id']==cid);actual=next(d for d in check.glob('final-mesh-readback-*') if d.is_dir() and json.loads((d/'mesh.json').read_text())['source_sha256']==entry['sha256']);j=json.loads((actual/'mesh.json').read_text());before=r/'jessie-rebase-v4'/('old-'+cid)
 files=[p.name for p in before.iterdir() if p.suffix in ['.f32','.u16','.u32','.rgba8']]
 for f in files:assert (actual/f).read_bytes()==(before/f).read_bytes(),(cid,f)
 b=(raw/cid).read_bytes();assert b== (r/'jessie-rebase-v4/chunks'/cid).read_bytes();assert j['lod_count']==4;assert len(b)-j['all_lods_end']==112;newref=next(p for p in newrefs if p['package']==entry['path']);outref=next(p for p in refs if p['chunk_sha256']==entry['sha256']);assert outref['bones']==newref['bones']
 if '/Hair/' not in entry['path']:
  slots=np.fromfile(actual/'triangle-materials.u16',dtype='<u2');assert set(slots)=={0,5};assert j['materials'][0]['package_index']==j['materials'][5]['package_index'];assert j['materials'][0]['name']=='Ally_Head' and j['materials'][5]['name']=='Ally_ArmsLegs'
 meshresults.append({'chunk':cid,'vertices':j['vertices'],'triangles':j['triangles'],'all_frozen_geometry_and_skin_streams_exact':files,'current_reference_bones_exact':j['skeleton_bones'],'lods':4,'current_build_post_LOD_tail_preserved_bytes':112})
by_path={'/Game/'+v['path'].split('/Content/',1)[1][:-7]:v for v in meta}
def resolve(v,index):
 assert index<0;b=(raw/v['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);obj=struct.unpack_from('<Q',b,s[7]+(-index-1)*8)[0];assert obj>>62==2;obj&=(1<<62)-1;pkg=v['imported_packages'][obj>>32];h=struct.unpack_from('<Q',b,s[6]+(obj&0xffffffff)*8)[0];target=by_path[pkg];bb=(raw/target['chunk_id']).read_bytes();ss=struct.unpack_from('<15I',bb);assert h in [struct.unpack_from('<Q',bb,i+56)[0] for i in range(ss[8],ss[9],72)];return pkg
body=next(v for v in meta if v['chunk_id']=='911395b71b48cf1a00000001');bodydir=next(d for d in check.glob('final-mesh-readback-*') if d.is_dir() and json.loads((d/'mesh.json').read_text())['source_sha256']==body['sha256']);j=json.loads((bodydir/'mesh.json').read_text());mi_path=resolve(body,j['materials'][0]['package_index']);assert mi_path==resolve(body,j['materials'][5]['package_index']);mi=by_path[mi_path];b=(raw/mi['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);needle=struct.pack('<I',4)+b'\x00\x07\x00\x07';hits=[p for p in range(s[1],min(s[1]+700,len(b)-8)) if b[p:p+8]==needle];assert len(hits)==1;p=hits[0]+4;bindings=[]
for i in range(4):
 param=mi['name_map'][struct.unpack_from('<I',b,p+4)[0]];target=resolve(mi,struct.unpack_from('<i',b,p+17)[0]);assert target.startswith('/Game/_Jessie0/');bindings.append({'parameter':param,'texture':target});p+=37
assert [x['parameter'] for x in bindings]==['Albedo','Normal','RMA','SSSMask'];assert '/Game/_Augusta/Art/Characters/Materials/MM_Character' in mi['imported_packages'];assert '/Game/_Augusta/Art/Characters/Player_Male01/Textures/ssprofile_male01_Max_apparel' in mi['imported_packages'];mips=0
for t in build['textures']:
 suffix=t['private_path'][:-7].rsplit('_',1)[-1];directory=check/('final-mips-T_Jes_Apparel_01_'+suffix);data=json.loads((directory/'texture.json').read_text());assert data['pixel_format']==t['format'] and data['width']==t['width'];assert len(data['mips'])==len(t['mips'])
 for item in t['mips']:
  name='mip-%02d.bin'%item['level'];actual=(directory/name).read_bytes();assert actual==(r/'jessie-complete-v1/expected-mips'/suffix/name).read_bytes();assert hashlib.sha256(actual).hexdigest()==item['sha256'];mips+=1
assert mips==47
for v in meta:
 b=(raw/v['chunk_id']).read_bytes();legacy=check/'final-readback-legacy'/v['path'].replace('../../../','');assert legacy.with_suffix('.uexp').read_bytes()==b[struct.unpack_from('<I',b,4)[0]:]
c=(check/'final-mips-T_Jes_Apparel_01_C/mip-00.bin').read_bytes();pixels=np.frombuffer(texture2ddecoder.decode_bc1(c,2048,2048),dtype='u1').reshape(2048,2048,4)[:,:,[2,1,0,3]];assert np.all(pixels[:,:,3]==255);Image.fromarray(pixels).save(check/'actual-decoded-atlas.png');assert (r/'jessie-complete-v1/decoded-Jessie-atlas.png').read_bytes()==(check/'actual-decoded-atlas.png').read_bytes();result={'status':'PASS_OFFLINE_WINDOWS_PENDING','scope':'Jessie/Hoops only; no runtime mod','current_build':'UE5.7.4 Augusta-CL-3207493','meshes':meshresults,'current_template_texture_mips_verified':mips,'head_body_same_private_material':mi_path,'private_texture_bindings_public_export_hashes_resolved':bindings,'legacy_exports_match_final_Zen_native_payloads':len(meta),'stock_master_and_subsurface_imports_preserved':True,'source_model_fit_weights_UVs_and_FP_split_unchanged':True,'color_atlas_resolution':2048,'full_mapped_UObject_deserialization':'Not performed; object prefixes copied from current original templates','runtime':'NOT TESTED; native parsing/container hashes do not prove Windows engine loading'};(r/'jessie-final-validation-v1.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS:6 meshes,47 mips,11 exports,actual private material/hash bindings')
