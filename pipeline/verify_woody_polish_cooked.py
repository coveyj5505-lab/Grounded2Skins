"""Fresh Blender/cooked agreement and independent private material/mip checks."""
import bpy,numpy as np,json,sys,hashlib,struct
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];root=Path(args[0]);check=Path(args[1]) if len(args)>1 else root/'check-v2';build=Path(args[2]) if len(args)>2 else root/'build-v2';o=bpy.data.objects['Woody_Skinned'];expected=np.load(build/'buffers/expected.npz');order=np.argsort(expected['source_triangles']);meta=json.loads((check/'final-metadata.json').read_text());target=next(m for m in meta if m['chunk_id']=='b0baaf49556b7e2200000001');d=next(d for d in check.glob('final-mesh-readback-*') if (d/'mesh.json').exists() and json.loads((d/'mesh.json').read_text())['source_sha256']==target['sha256']);idx=np.fromfile(d/'indices.u32',dtype='<u4').reshape(-1,3)[order];points=np.fromfile(d/'positions.f32',dtype='<f4').reshape(-1,3)*[.01,-.01,.01];normals=np.fromfile(d/'normals.f32',dtype='<f4').reshape(-1,3)*[1,-1,1];normals/=np.linalg.norm(normals,axis=1,keepdims=True);m=o.data;m.calc_loop_triangles();tri=np.array([t.vertices[:] for t in m.loop_triangles]);p=np.array([v.co[:] for v in m.vertices]);err=float(np.max(abs(p[tri]-points[idx])));assert err<2e-6
loop_normals=np.zeros((len(m.loops),3));seen=np.zeros(len(m.loops),bool)
for t,ns in zip(m.loop_triangles,normals[idx]):
 for li,n in zip(t.loops,ns):
  if seen[li]:assert np.max(abs(loop_normals[li]-n))<.009
  loop_normals[li]=n;seen[li]=True
assert seen.all();m.normals_split_custom_set(loop_normals.tolist())
# Resolve actual public export hashes; every private texture dependency exists.
by_path={'/Game/'+v['path'].split('/Content/',1)[1][:-7]:v for v in meta};raw=check/'final-unpacked/chunks'
def resolve(v,index):
 assert index<0;b=(raw/v['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);x=struct.unpack_from('<Q',b,s[7]+(-index-1)*8)[0];assert x>>62==2;x&=(1<<62)-1;pkg=v['imported_packages'][x>>32];h=struct.unpack_from('<Q',b,s[6]+(x&0xffffffff)*8)[0];t=by_path[pkg];bb=(raw/t['chunk_id']).read_bytes();ss=struct.unpack_from('<15I',bb);assert h in [struct.unpack_from('<Q',bb,i+56)[0] for i in range(ss[8],ss[9],72)];return pkg
j=json.loads((d/'mesh.json').read_text());mi_path=resolve(target,j['materials'][0]['package_index']);assert mi_path==resolve(target,j['materials'][3]['package_index']);mi=by_path[mi_path];b=(raw/mi['chunk_id']).read_bytes();s=struct.unpack_from('<15I',b);needle=struct.pack('<I',4)+b'\x00\x07\x00\x07';ats=[i for i in range(s[1],s[1]+600) if b[i:i+8]==needle];assert len(ats)==1;q=ats[0]+4;bindings=[]
for i in range(4):
 name=mi['name_map'][struct.unpack_from('<I',b,q+4)[0]];tex=resolve(mi,struct.unpack_from('<i',b,q+17)[0]);assert '/_Woody00/' in tex;bindings.append({'parameter':name,'texture':tex});q+=37
assert [v['parameter'] for v in bindings]==['Albedo','Normal','RMA','SSSMask'];assert '/Game/_Augusta/Art/Characters/Materials/MM_Character' in mi['imported_packages']
count=0
for folder in check.glob('final-mips-*'):
 old=Path('/workspace/mod-work/woody-stage/final-check-v1')/folder.name;jj=json.loads((folder/'texture.json').read_text());orig=json.loads((old/'texture.json').read_text());assert jj['mips']==orig['mips']
 for mip in jj['mips']:
  f='mip-%02d.bin'%mip['level'];assert (folder/f).read_bytes()==(old/f).read_bytes();count+=1
assert count==50
# Complete Zen->legacy payload round-trip for every material/mesh/texture.
for v in meta:
 bb=(raw/v['chunk_id']).read_bytes();legacy=check/'final-readback-legacy'/v['path'].replace('../../../','');assert legacy.with_suffix('.uexp').read_bytes()==bb[struct.unpack_from('<I',bb,4)[0]:]
assert len(o.find_armature().data.bones)==188;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(root/'Woody-Polish-Cooked-Verified.blend'),compress=True)
r={'status':'PASS_OFFLINE','fresh_source_vs_cooked_corners':int(idx.size),'max_position_error_m':err,'preview_normals':'Actual independent CUE4Parse cooked readback','head_and_body_resolve_same_existing_private_material':mi_path,'material_bindings_public_export_hashes_verified':bindings,'all_texture_mips_read_back_and_identical_to_original_release':count,'all_legacy_export_payloads_exact':len(meta),'native_reference_bones':188,'runtime':'NOT TESTED'};(root/'cooked-source-material-validation.json').write_text(json.dumps(r,indent=2)+'\n');print('COOKED_WOODY_SOURCE_MATERIALS_PASS',err,count)
