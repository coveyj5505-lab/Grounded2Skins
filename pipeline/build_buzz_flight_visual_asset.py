"""Private full-flight cosmetic asset from proven rigid accessory serialization.
No stable character assets or released runtime are changed.
"""
import argparse,json,struct,hashlib,subprocess,sys
from pathlib import Path
import numpy as np
from native_buffers import encode,skeleton_signature
from assemble_bopeep_zen import batch,H
from compare_stock_max import names
from write_buzz_atlas_textures import layout,encode as encode_texture
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('baked',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.mkdir(exist_ok=False);out=a.out;root=Path('/workspace/mod-work');source=root/'wings-stage/proven-package-v2/unpacked';check=root/'wings-stage/proven-readback-v2';cid='921071aca481007100000001';original=(source/'chunks'/cid).read_bytes();profile=next(json.loads((d/'mesh.json').read_text()) for d in check.glob('final-mesh-readback-*') if (d/'mesh.json').exists() and json.loads((d/'mesh.json').read_text())['source_sha256']==hashlib.sha256(original).hexdigest());profile['chunk']=cid;assert profile['skeleton_bones']==192
reference=root/'crook-stage/reference.json';data=dict(np.load(a.baked/'geometry.npz'));data['material_count']=np.array(len(profile['materials']));np.savez_compressed(out/'geometry.npz',**data);encode(data,skeleton_signature(reference),out/'buffers');(out/'profiles.json').write_text(json.dumps([profile],indent=2)+'\n')
subprocess.run([sys.executable,str(Path(__file__).parent/'rewrite_measured_native_lods.py'),str(source),str(out/'profiles.json'),str(out/'buffers'),str(reference),str(out/'rewritten')],check=True)
(out/'raw/chunks').mkdir(parents=True);oldpkg='/Game/_BzWExt1/Art/Characters/Player_Female01/SK_Female_Teen_01';newpkg=oldpkg.replace('_BzWExt1','_BzFlit1');paths={};manifest=json.loads((source/'manifest.json').read_text())
for c,path in manifest['chunk_paths'].items():
 if c!=cid and '/_BzWing0/' not in path:continue
 b=(out/'rewritten/chunks'/c).read_bytes() if c==cid else (source/'chunks'/c).read_bytes();newpath=path.replace('_BzWExt1','_BzFlit1').replace('_BzWing0','_BzFMat1');newpackage='/Game/'+newpath.split('/Content/',1)[1].rsplit('.',1)[0];newcid=H(newpackage).to_bytes(8,'little').hex()+c[16:]
 if path.endswith('.uasset'):
  b=bytearray(b);s=struct.unpack_from('<15I',b)
  for at in [60,s[12]]:
   ns,end=names(b,at);encoded=batch([n.replace('_BzWExt1','_BzFlit1').replace('_BzWing0','_BzFMat1') for n in ns]);assert len(encoded)==end-at;b[at:end]=encoded
 (out/'raw/chunks'/newcid).write_bytes(b);paths[newcid]=newpath
# Replace only albedo mip bytes in the new private namespace. All dimensions,
# flags, mip offsets, shader/material bytes and unrelated textures stay exact.
albedo=next(c for c,p in paths.items() if p.endswith('T_Wng_Apparel_01_C.uasset'));bulkcid=albedo[:16]+'00000002';export=out/'raw/chunks'/albedo;bulkfile=out/'raw/chunks'/bulkcid;oldexport=export.read_bytes();oldbulk=bulkfile.read_bytes();info=layout(oldexport);assert info['format']=='PF_DXT5';image=Image.open(a.baked/'Flight-basecolor-atlas.png').convert('RGBA');assert image.size==(4096,4096);eb=bytearray(oldexport);ub=bytearray(oldbulk);mips=[]
for mip in info['mips']:
 payload=encode_texture(image.resize((mip['width'],mip['height']),Image.Resampling.LANCZOS),'PF_DXT5');assert len(payload)==mip['bytes'];target=eb if mip['inline'] else ub;target[mip['offset']:mip['offset']+mip['bytes']]=payload;mips.append({**mip,'sha256':hashlib.sha256(payload).hexdigest()})
for old,new,inline in [(oldexport,eb,True),(oldbulk,ub,False)]:
 assert len(old)==len(new);mask=np.zeros(len(old),bool)
 for mip in info['mips']:
  if mip['inline']==inline:mask[mip['offset']:mip['offset']+mip['bytes']]=True
 assert not np.any((np.frombuffer(old,'u1')!=np.frombuffer(new,'u1'))&~mask)
export.write_bytes(eb);bulkfile.write_bytes(ub);(out/'atlas-mips.json').write_text(json.dumps({'source_image_sha256':hashlib.sha256((a.baked/'Flight-basecolor-atlas.png').read_bytes()).hexdigest(),'albedo_chunk':albedo,'mips':mips,'only_measured_mip_bytes_changed':True},indent=2)+'\n')
entries={}
for c,path in paths.items():
 if not path.endswith('.uasset'):continue
 b=(out/'raw/chunks'/c).read_bytes();s=struct.unpack_from('<15I',b);ns,end=names(b,s[12]);nums=struct.unpack_from('<'+'i'*len(ns),b,end);entries[int.from_bytes(bytes.fromhex(c[:16]),'little')]=[H(n if v==0 else n+'_'+str(v-1)) for n,v in zip(ns,nums)]
entries=dict(sorted(entries.items()));store=bytearray(16*len(entries))
for i,imports in enumerate(entries.values()):
 if imports:struct.pack_into('<II',store,i*16,len(imports),len(store)-i*16);store.extend(struct.pack('<'+'Q'*len(imports),*imports))
header=next((source/'chunks').glob('*00000006'));b=bytearray(header.read_bytes()[:16]+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(store))+store+bytes(20));b.extend(struct.pack('<qqI',len(b)+16,4,0));(out/'raw/chunks'/header.name).write_bytes(b);(out/'raw/manifest.json').write_text(json.dumps(dict(manifest,chunk_paths=paths),indent=2)+'\n');report={'status':'BUILT_NATIVE_READBACK_PENDING','asset':newpkg+'.SK_Female_Teen_01','chunk':H(newpkg).to_bytes(8,'little').hex()+'00000001','material_namespace':'/Game/_BzFMat1/','body_and_deployed_wings_in_single_visual':True,'source_v03_files_changed':False,'requires_runtime_adapter':True,'standalone_playable_feature':False};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
