"""Fresh cooked readback and exact per-triangle attribute preservation checks."""
import argparse,json,hashlib,struct,shutil
from pathlib import Path
import numpy as np
from build_first_person_sections import CONFIG,run,DOTNET,PIPE
from compare_stock_max import names
from extract_reference_skeleton import extract

def validate(character,root,reuse=False):
 c=CONFIG[character];stage=c['stage'];raw=root/'package/unpacked';manifest=json.loads((raw/'manifest.json').read_text());base=json.loads((root/'baseline-profiles.json').read_text());meta=[];skeletons=[];refs=json.loads((stage/'final-skeletons.json').read_text())['meshes']
 for p in base:
  cid=p['chunk'];b=(raw/'chunks'/cid).read_bytes();s=struct.unpack_from('<15I',b);nm,_=names(b,60);imp,end=names(b,s[12]);nums=struct.unpack_from('<'+'i'*len(imp),b,end);imports=[v if n==0 else v+'_'+str(n-1) for v,n in zip(imp,nums)];m={'path':manifest['chunk_paths'][cid],'chunk_id':cid,'name_map':nm,'imported_packages':imports};meta.append(m);sk=extract(b,nm);sk.update(package=m['path'],chunk_sha256=hashlib.sha256(b).hexdigest());original=next(x for x in refs if x['chunk_sha256']==p['source_sha256']);assert json.loads(json.dumps(sk['bones']))==original['bones'];skeletons.append(sk)
 (root/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');(root/'skeletons.json').write_text(json.dumps({'meshes':skeletons},indent=2)+'\n');newexp=np.load(root/'buffers/expected.npz');oldbuffers=stage/('native-buffers' if character=='Buzz' else '../buffers-v4' if character=='Jessie' else '../buffers-v1');oldexp=np.load(oldbuffers/'expected.npz');reports=[]
 oldsort=np.argsort(oldexp['source_triangles']);newsort=np.argsort(newexp['source_triangles']);assert np.array_equal(np.sort(newexp['source_triangles']),np.arange(len(newsort))) and len(oldsort)==len(newsort)
 for p,m in zip(base,meta):
  cid=p['chunk'];dest=root/('readback-'+cid);
  if not dest.exists():run([DOTNET,PIPE/'native-lod-probe/bin/Release/net10.0/NativeLodProbe.dll',raw/'chunks'/cid,root/'skeletons.json',root/'metadata.json',dest],root/(cid+'-readback.log'))
  else:assert reuse,'Existing readback requires explicit reuse'
  n=json.loads((dest/'mesh.json').read_text());assert n['source_sha256']==hashlib.sha256((raw/'chunks'/cid).read_bytes()).hexdigest();baseline=root/('baseline-'+cid);read=lambda folder,file,dtype,cols:np.fromfile(folder/file,dtype=dtype).reshape(-1,cols)
  oldindex=read(baseline,'indices.u32','<u4',3)[oldsort];newindex=read(dest,'indices.u32','<u4',3)[newsort];verified=[]
  for file,dtype,cols in [('positions.f32','<f4',3),('uv0.f32','<f4',2),('normals.f32','<f4',3),('joints.u16','<u2',8),('weights.u16','<u2',8),('colors.rgba8','u1',4)]:
   a=read(baseline,file,dtype,cols)[oldindex];b=read(dest,file,dtype,cols)[newindex];assert np.array_equal(a,b),(character,cid,file,float(np.max(abs(a.astype(float)-b))));verified.append(file)
  oldstatic=(oldbuffers/'static-vertices.bin').read_bytes();newstatic=(root/'buffers/static-vertices.bin').read_bytes();oldpayload=(stage/c['raw']/'chunks'/cid).read_bytes();newpayload=(raw/'chunks'/cid).read_bytes();assert oldpayload.count(oldstatic)==p['lod_count'] and newpayload.count(newstatic)==p['lod_count'];oldn=p['vertices'];newn=n['vertices'];oldframes=np.frombuffer(oldstatic[26:26+oldn*8],dtype='u1').reshape(oldn,8);newframes=np.frombuffer(newstatic[26:26+newn*8],dtype='u1').reshape(newn,8);assert np.array_equal(oldframes[oldindex],newframes[newindex]);verified.append('actual_packed_tangent_normal_handedness_bytes')
  # Read-back slots refer to the SAME mod-private atlas material as the old
  # body, so separating geometry introduces no stock texture dependence.
  head=n['materials'][c['head_slot']];body=n['materials'][c.get('body_slot',0)];assert head['package_index']==body['package_index']==p['materials'][0]['package_index']
  assert n['lod_count']==p['lod_count'];payload=(raw/'chunks'/cid).read_bytes();blocks=[payload[x['start']:x['end']] for x in n['lods']];assert all(x==blocks[0] for x in blocks)
  assigned=read(dest,'triangle-materials.u16','<u2',1).ravel();inputmesh=np.load(root/'geometry.npz');assert np.array_equal(assigned,inputmesh['materials'][newexp['source_triangles']]);assert set(assigned)=={c.get('body_slot',0),c['head_slot']}
  oldmeta=next(x for x in json.loads((stage/'final-metadata.json').read_text()) if x['chunk_id']==cid);assert oldmeta['imported_packages']==m['imported_packages'];index=body['package_index'];s=struct.unpack_from('<15I',payload);obj=struct.unpack_from('<Q',payload,s[7]+(-index-1)*8)[0];assert obj>>62==2;v=obj&((1<<62)-1);private=m['imported_packages'][v>>32];assert any(token in private for token in ['/_BuzzMod/','/_Woody00/','/_BoPeep0/','/_Jessie0/'])
  for slot,name in c['names'].items():assert n['materials'][slot]['name']==name
  reports.append({'chunk':cid,'LOD_count':n['lod_count'],'vertices':n['vertices'],'triangles':n['triangles'],'head_slot':head['slot'],'head_slot_name':head['name'],'body_slot':c.get('body_slot',0),'both_slots_resolve_same_private_material':private,'all_original_triangle_corner_attributes_exact':verified,'original_bone_hierarchy_rest_exact':True,'all_LODs_independently_read':True})
 # Retoc may report skipped assets while returning exit0: require each
 # expected native export payload below, not merely the process result.
 # All other chunks, including shader payloads, textures, hair and menu meshes,
 # are byte-exact to the user-tested baseline (excluding new container ID).
 before=stage/c['raw']/'chunks';after=raw/'chunks';a={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in before.iterdir() if not p.name.endswith('00000006')};b={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in after.iterdir() if not p.name.endswith('00000006')};assert a.keys()==b.keys();changed=[k for k in a if a[k]!=b[k]];assert sorted(changed)==sorted(c['body'])
 legacyinput=root/'legacy-input';legacyinput.mkdir(exist_ok=reuse)
 for p in list((root/'package/mod').iterdir())+list(Path('/workspace/mod-work/global-stage/input').glob('global.*')):shutil.copyfile(p,legacyinput/p.name)
 if not (root/'legacy').exists():run(['/workspace/mod-work/bin/retoc','to-legacy',legacyinput,root/'legacy','--no-shaders','--no-script-objects','--no-parallel'],root/'legacy.log')
 else:assert reuse,'Existing legacy read requires explicit reuse'
 for m in meta:
  p=root/'legacy'/m['path'].replace('../../../','');payload=(raw/'chunks'/m['chunk_id']).read_bytes();header=struct.unpack_from('<I',payload,4)[0];assert p.with_suffix('.uexp').read_bytes()==payload[header:]
 report={'character':character,'status':'passed_offline','meshes':reports,'only_changed_mesh_chunks':changed,'other_material_shader_texture_hair_menu_chunks_exact_baseline':len(a)-len(changed),'camera_offsets_animations_physics_or_network_state_changed':False,'full_head_geometry_retained':True,'legacy_native_payloads_roundtrip_exact':True,'runtime':'NOT TESTED; Windows first/third-person switch and multiplayer visibility require user validation'};(root/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('character',choices=CONFIG);p.add_argument('stage',type=Path);p.add_argument('--reuse-readback',action='store_true');a=p.parse_args();validate(a.character,a.stage,a.reuse_readback)
