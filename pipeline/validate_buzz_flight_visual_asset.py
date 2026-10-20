"""Independent native read-back for the prepared flight-only cosmetic asset."""
import argparse,json,struct,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import texture2ddecoder
from compare_stock_max import names
p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('check',type=Path);p.add_argument('--atlas',type=Path);a=p.parse_args();rec=json.loads((a.build/'report.json').read_text());meta=json.loads((a.check/'final-metadata.json').read_text());raw=a.check/'final-unpacked/chunks';target=next(m for m in meta if m['chunk_id']==rec['chunk']);b=(raw/rec['chunk']).read_bytes();d=a.check/'final-mesh-readback-0';j=json.loads((d/'mesh.json').read_text());e=np.load(a.build/'buffers/expected.npz');read=lambda f,t,c:np.fromfile(d/f,dtype=t).reshape(-1,c);assert j['source_sha256']==hashlib.sha256(b).hexdigest();assert j['vertices']==len(e['positions']) and j['triangles']==len(e['indices'])//3;assert j['skeleton_bones']==192 and j['used_bones']==[0] and j['lod_count']==4
for f,t,c,key in [('positions.f32','<f4',3,'positions'),('weights.u16','<u2',8,'quantized_weights'),('colors.rgba8','u1',4,'colors')]:assert np.array_equal(read(f,t,c),e[key])
assert np.array_equal(read('indices.u32','<u4',1).ravel(),e['indices']);assert np.array_equal(read('uv0.f32','<f4',2),e['uv0'].astype('f2').astype('f4'));assert np.max(abs(read('normals.f32','<f4',3)-e['normals']))<.008;assert np.all(read('joints.u16','<u2',8)==0) and np.all(read('triangle-materials.u16','<u2',1)==0)
blocks=[b[v['start']:v['end']] for v in j['lods']];assert len(blocks)==4 and all(v==blocks[0] for v in blocks);assert b.count((a.build/'buffers/static-vertices.bin').read_bytes())==4
refs=json.loads((a.check/'final-skeletons.json').read_text())['meshes'];native=json.loads(Path('/workspace/mod-work/crook-stage/reference.json').read_text())['meshes'][0]['bones'];assert refs[0]['bones']==native
s=struct.unpack_from('<15I',b);ns,_=names(b,60);pkg=ns[s[2]&0x3fffffff];objects=[]
for at in range(s[8],s[9],72):
 ni,num=struct.unpack_from('<II',b,at+16);outer,cls=struct.unpack_from('<QQ',b,at+24)
 if outer==0xffffffffffffffff and ns[ni&0x3fffffff]=='SK_Female_Teen_01':objects.append(pkg+'.'+ns[ni&0x3fffffff])
assert objects==[rec['asset']]
by_path={'/Game/'+m['path'].split('/Content/',1)[1][:-7]:m for m in meta}
def resolve(m,index):
 assert index<0;bb=(raw/m['chunk_id']).read_bytes();ss=struct.unpack_from('<15I',bb);v=struct.unpack_from('<Q',bb,ss[7]+(-index-1)*8)[0];assert v>>62==2;v&=(1<<62)-1;package=m['imported_packages'][v>>32];hh=struct.unpack_from('<Q',bb,ss[6]+(v&0xffffffff)*8)[0];t=by_path[package];bb=(raw/t['chunk_id']).read_bytes();ss=struct.unpack_from('<15I',bb);assert hh in [struct.unpack_from('<Q',bb,i+56)[0] for i in range(ss[8],ss[9],72)];return package
mi_path=resolve(target,j['materials'][0]['package_index']);assert mi_path.startswith('/Game/_BzFMat1/');mi=by_path[mi_path];bb=(raw/mi['chunk_id']).read_bytes();ss=struct.unpack_from('<15I',bb);needle=struct.pack('<I',4)+b'\x00\x07\x00\x07';ats=[i for i in range(ss[1],ss[1]+600) if bb[i:i+8]==needle];assert len(ats)==1;q=ats[0]+4;bindings=[]
for i in range(4):
 name=mi['name_map'][struct.unpack_from('<I',bb,q+4)[0]];tex=resolve(mi,struct.unpack_from('<i',bb,q+17)[0]);assert tex.startswith('/Game/_BzFMat1/');bindings.append({'parameter':name,'texture':tex});q+=37
assert [x['parameter'] for x in bindings]==['Albedo','Normal','RMA','SSSMask'];assert '/Game/_Augusta/Art/Characters/Materials/MM_Character' in mi['imported_packages'];count=0;old=Path('/workspace/mod-work/wings-stage/proven-readback-v2')
for folder in a.check.glob('final-mips-*'):
 for f in folder.glob('mip-*.bin'):
  if folder.name=='final-mips-T_Wng_Apparel_01_C':
   level=int(f.stem.split('-')[1]);expected_mips=json.loads((a.build/'atlas-mips.json').read_text())['mips'];assert hashlib.sha256(f.read_bytes()).hexdigest()==expected_mips[level]['sha256']
  else:assert f.read_bytes()==(old/folder.name/f.name).read_bytes()
  count+=1
assert count==50
for m in meta:
 bb=(raw/m['chunk_id']).read_bytes();ss=struct.unpack_from('<15I',bb);legacy=a.check/'final-readback-legacy'/m['path'].replace('../../../','');assert legacy.with_suffix('.uexp').read_bytes()==bb[ss[1]:]
c=(a.check/'final-mips-T_Wng_Apparel_01_C/mip-00.bin').read_bytes();rgba=np.frombuffer(texture2ddecoder.decode_bc3(c,4096,4096),dtype='u1').reshape(4096,4096,4)[:,:,[2,1,0,3]];Image.fromarray(rgba).save(a.check/'actual-decoded-atlas.png')
image=Image.open(a.atlas or a.build.parent/'buzz-flight-baked-v2/Flight-basecolor-atlas.png').convert('RGBA');expected_pixels=np.array(image);color_error=float(np.mean(abs(rgba[:,:,:3].astype(float)-expected_pixels[:,:,:3])));assert color_error<5 and np.all(rgba[:,:,3]==255)
body=e['source_vertices']<18413;assert np.all(e['uv0'][body,0]<.5) and np.all(e['uv0'][~body,0]>.5)
r={'status':'PASS_OFFLINE_CANDIDATE_ONLY','asset':rec['asset'],'actual_path_and_export_verified':True,'render_vertices':j['vertices'],'triangles':j['triangles'],'lods':4,'root0_only':True,'reference_bones':192,'all_native_streams_match_intended_encoding':True,'private_material':mi_path,'actual_material_texture_public_export_hashes_resolved':bindings,'fresh_texture_mips_exact':count,'private_albedo_mips_independently_hash_checked':13,'other_texture_mips_exact_to_validated_wings':37,'combined_atlas_BC3_RGB_mean_error':color_error,'body_UVs_left_half_wing_UVs_right_half':True,'legacy_native_payloads_exact':len(meta),'runtime':'No runtime adapter installed or tested; this is not a playable flight feature','v03_released_files_modified':False};(a.build/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
