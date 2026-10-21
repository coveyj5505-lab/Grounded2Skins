"""Clone the actual current-build Max atlas MI into a private skin namespace.
Uses new native properties; no5.6 material payload is reused.
"""
import argparse,json,struct,hashlib
from pathlib import Path
from compare_stock_max import names
from assemble_jessie_zen import batch,H
p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--namespace',default='_Jessie0');p.add_argument('--tag',default='Jes');a=p.parse_args();assert len(a.namespace)==8 and len(a.tag)==3;a.out.mkdir(exist_ok=False)
r=Path('/workspace/mod-work/ue57-migration/Max');meta=json.loads((r/'metadata.json').read_text());m=next(v for v in meta if v['path'].endswith('/MI_Character_Male01_Max_Apparel01.uasset'));raw=(r/'chunks'/m['chunk_id']).read_bytes();b=bytearray(raw);s=struct.unpack_from('<15I',b)
oldshort=['MI_Character_Male01_Max_Apparel01']+['T_Max_Apparel_01_'+x for x in ['C','N','RMA','SSS']]
base='/Game/_Augusta/Art/Characters/Player_Male01/Textures/'
replacements={n:n.replace('_Max_','_'+a.tag+'_') for n in oldshort}
for n in oldshort:
 old=base+n;new=old.replace('/_Augusta/','/'+a.namespace+'/').replace('_Max_','_'+a.tag+'_');replacements[old]=new;replacements[old.replace('/Game/','../../../Augusta/Content/')]=new.replace('/Game/','../../../Augusta/Content/')
def rename(v):return replacements.get(v,v)
hashes={H(n):H(rename(n)) for n in oldshort}
for at in [60,s[12]]:
 ns,end=names(b,at);new=[rename(n) for n in ns];encoded=batch(new);assert len(encoded)==end-at;b[at:end]=encoded
for at in range(s[6],s[7],8):
 h=struct.unpack_from('<Q',b,at)[0]
 if h in hashes:struct.pack_into('<Q',b,at,hashes[h])
for at in range(s[8],s[9],72):
 h=struct.unpack_from('<Q',b,at+56)[0]
 if h in hashes:struct.pack_into('<Q',b,at+56,hashes[h])
assert b[s[1]:]==raw[s[1]:];path=rename(m['path'][:-7])+'.uasset';package='/Game/'+path.split('/Content/',1)[1][:-7];assert package in names(b,60)[0];cid=H(package).to_bytes(8,'little').hex()+'00000001';(a.out/cid).write_bytes(b);imp,end=names(b,s[12]);nums=struct.unpack_from('<'+'i'*len(imp),b,end);imp=[n if v==0 else n+'_'+str(v-1) for n,v in zip(imp,nums)];dependencies=[v for v in imp if '/'+a.namespace+'/' in v];assert len(dependencies)==4;report={'status':'CURRENT_BUILD_MATERIAL_READY_TEXTURES_PENDING','path':path,'chunk':cid,'sha256':hashlib.sha256(b).hexdigest(),'source_sha256':m['sha256'],'new_57_native_material_payload_preserved_exact':True,'private_texture_dependencies':dependencies,'missing_input':'Four current-build source texture templates, deliberately not guessed from5.6'};(a.out/'material-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
