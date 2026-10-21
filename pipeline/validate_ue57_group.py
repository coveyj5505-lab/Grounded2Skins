"""Final actual-package checks for skin and cosmetic asset5.7 migrations."""
import argparse,json,hashlib,struct
from pathlib import Path
import numpy as np
from PIL import Image
import texture2ddecoder
from ue57_skin_config import CONFIG as SKINS
from ue57_accessory_config import CONFIG as ACCESSORIES
CONFIG={**SKINS,**ACCESSORIES};p=argparse.ArgumentParser();p.add_argument('group',choices=CONFIG);p.add_argument('rebase',type=Path);p.add_argument('check',type=Path);p.add_argument('--complete',type=Path);p.add_argument('--dependency-check',type=Path);a=p.parse_args();c=CONFIG[a.group];meta=json.loads((a.check/'final-metadata.json').read_text());refs=json.loads((a.check/'final-skeletons.json').read_text())['meshes'];raw=a.check/'final-unpacked/chunks';records=json.loads((a.rebase/'mesh-validation.json').read_text())['meshes'];results=[];by_path={};where={}
for check in [a.check]+([a.dependency_check] if a.dependency_check else []):
 for m in json.loads((check/'final-metadata.json').read_text()):
  path='/Game/'+m['path'].split('/Content/',1)[1][:-7];by_path[path]=m;where[m['chunk_id']]=check/'final-unpacked/chunks'
def blob(v):return (where[v['chunk_id']]/v['chunk_id']).read_bytes()
def resolve(v,index):
 assert index<0;b=blob(v);s=struct.unpack_from('<15I',b);obj=struct.unpack_from('<Q',b,s[7]+(-index-1)*8)[0];assert obj>>62==2;obj&=(1<<62)-1;pkg=v['imported_packages'][obj>>32];h=struct.unpack_from('<Q',b,s[6]+(obj&0xffffffff)*8)[0];t=by_path[pkg];bb=blob(t);ss=struct.unpack_from('<15I',bb);assert h in [struct.unpack_from('<Q',bb,i+56)[0] for i in range(ss[8],ss[9],72)];return pkg
private=f'/Game/{c["namespace"]}/Art/Characters/Player_Male01/Textures/MI_Character_Male01_{c["tag"]}_Apparel01';seen_material=False
for item in records:
 cid=item['chunk'];m=next(m for m in meta if m['chunk_id']==cid);actual=next(d for d in a.check.glob('final-mesh-readback-*') if d.is_dir() and json.loads((d/'mesh.json').read_text())['source_sha256']==m['sha256']);old=a.rebase/('old-'+cid);j=json.loads((actual/'mesh.json').read_text());frozen=[]
 for f in old.iterdir():
  if f.suffix in ['.f32','.u16','.u32','.rgba8']:
   if f.name=='colors.rgba8' and item.get('old_has_colors',item['has_colors'])!=item['has_colors']:continue
   assert f.read_bytes()==(actual/f.name).read_bytes(),(cid,f.name);frozen.append(f.name)
 b=(raw/cid).read_bytes();assert b==(a.rebase/'chunks'/cid).read_bytes();assert j['lod_count']==4 and len(b)-j['all_lods_end']==112
 expected=json.loads((a.rebase/'rebased-input'/(cid+'.refs.json')).read_text())['meshes'][0];actualref=next(r for r in refs if r['chunk_sha256']==m['sha256']);assert actualref['bones']==expected['bones']
 body=a.group not in SKINS or not any(s in item['path'] for s in ['/Hair/','Peeper','Glasses'])
 if body:
  slots=c.get('slots',(0,));assert set(np.fromfile(actual/'triangle-materials.u16',dtype='<u2'))==set(slots)
  for slot in slots:assert resolve(m,j['materials'][slot]['package_index'])==private
  if a.group in SKINS:
   oldj=json.loads((old/'mesh.json').read_text());assert [j['materials'][slot]['name'] for slot in slots]==[oldj['materials'][slot]['name'] for slot in slots]
   if a.group=='Buzz':assert sum(v['name']==j['materials'][slots[1]]['name'] for v in j['materials'])==1
  else:assert j['used_bones']==[0]
  seen_material=True
 results.append({'chunk':cid,'vertices':j['vertices'],'triangles':j['triangles'],'bones':j['skeleton_bones'],'lods':4,'frozen_streams_exact':frozen,'private_material':private if body else None})
assert seen_material;mi=by_path[private];b=blob(mi);s=struct.unpack_from('<15I',b);needle=struct.pack('<I',4)+b'\x00\x07\x00\x07';hits=[i for i in range(s[1],min(s[1]+700,len(b)-8)) if b[i:i+8]==needle];assert len(hits)==1;at=hits[0]+4;bindings=[]
for i in range(4):
 name=mi['name_map'][struct.unpack_from('<I',b,at+4)[0]];tex=resolve(mi,struct.unpack_from('<i',b,at+17)[0]);assert tex.startswith('/Game/'+c['namespace']+'/');bindings.append({'parameter':name,'texture':tex});at+=37
assert [v['parameter'] for v in bindings]==['Albedo','Normal','RMA','SSSMask'];assert '/Game/_Augusta/Art/Characters/Materials/MM_Character' in mi['imported_packages'];assert '/Game/_Augusta/Art/Characters/Player_Male01/Textures/ssprofile_male01_Max_apparel' in mi['imported_packages'];mips=0
if a.complete:
 build=json.loads((a.complete/'build-report.json').read_text())
 for t in build['textures']:
  suffix=t['private_path'][:-7].rsplit('_',1)[-1];d=a.check/('final-mips-T_'+c['tag']+'_Apparel_01_'+suffix);jj=json.loads((d/'texture.json').read_text());assert jj['pixel_format']==t['format'] and len(jj['mips'])==len(t['mips'])
  for q in t['mips']:
   name='mip-%02d.bin'%q['level'];data=(d/name).read_bytes();assert data==(a.complete/'expected-mips'/suffix/name).read_bytes();assert hashlib.sha256(data).hexdigest()==q['sha256'];mips+=1
 assert mips==47;payload=(a.check/('final-mips-T_'+c['tag']+'_Apparel_01_C/mip-00.bin')).read_bytes();px=np.frombuffer(texture2ddecoder.decode_bc1(payload,2048,2048),dtype='u1').reshape(2048,2048,4)[:,:,[2,1,0,3]];assert np.all(px[:,:,3]==255);Image.fromarray(px).save(a.check/'actual-decoded-atlas.png')
for m in meta:
 b=blob(m);legacy=a.check/'final-readback-legacy'/m['path'].replace('../../../','');assert legacy.with_suffix('.uexp').read_bytes()==b[struct.unpack_from('<I',b,4)[0]:]
report={'group':a.group,'status':'PASS_OFFLINE_WINDOWS_PENDING','current_build':'UE5.7.4 Augusta-CL-3207493','meshes':results,'private_material':private,'verified_private_bindings':bindings,'mips_checked':mips,'cross_package_dependency':str(a.dependency_check) if a.dependency_check else None,'legacy_exports_exact':len(meta),'shape_weights_UVs_FP_sections_preserved':True,'runtime':'NOT TESTED; container/native readback alone is not engine-load or accessory-function proof'};(a.check/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',a.group,len(results),'meshes,',mips,'mips')
