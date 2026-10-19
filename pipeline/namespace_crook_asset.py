"""Clone only the new crook mesh into a private package; never override Willow."""
import argparse,json,struct,hashlib
from pathlib import Path
from cityhash import CityHash64
from compare_stock_max import names
from assemble_bopeep_zen import batch,H
p=argparse.ArgumentParser();p.add_argument('cooked',type=Path);p.add_argument('template',type=Path);p.add_argument('out',type=Path);a=p.parse_args();assert not a.out.exists();(a.out/'chunks').mkdir(parents=True)
cid='2ee2517f02d2199900000001';raw=(a.cooked/'chunks'/cid).read_bytes();strings,end=names(raw,60);assert batch(strings)==raw[60:end], 'Name batch format differs'
old='/Game/_Augusta/Art/Characters/Player_Female01/SK_Female_Teen_01';new=old.replace('/_Augusta/','/_BoCrook/');assert strings.count(old)==1;updated=[new if n==old else n for n in strings];replacement=batch(updated);assert len(replacement)==end-60
b=raw[:60]+replacement+raw[end:];assert b[end:]==raw[end:]
newid=H(new);newcid=newid.to_bytes(8,'little').hex()+'00000001';(a.out/'chunks'/newcid).write_bytes(b)
s=struct.unpack_from('<15I',b);imports,footer=names(b,s[12]);numbers=struct.unpack_from('<'+'i'*len(imports),b,footer);assert len(b[footer:s[1]])==len(imports)*4
imp=[H(v if n==0 else v+'_'+str(n-1)) for v,n in zip(imports,numbers)]
store=struct.pack('<II',len(imp),16)+bytes(8)+struct.pack('<'+'Q'*len(imp),*imp)
oldheader=next((a.template/'chunks').glob('*00000006'));prefix=oldheader.read_bytes()[:16]
head=bytearray(prefix+struct.pack('<IQI',1,newid,len(store))+store+bytes(20));head.extend(struct.pack('<qqI',len(head)+16,4,0));(a.out/'chunks'/oldheader.name).write_bytes(head)
manifest=json.loads((a.template/'manifest.json').read_text());manifest['chunk_paths']={newcid:'../../../Augusta/Content/'+new.removeprefix('/Game/')+'.uasset'};(a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
report={'package':new,'object':new+'.'+new.rsplit('/',1)[1],'chunk':newcid,'packages':1,'chunks':2,'old_self_package':old,'self_name_relocation_only':True,'native_payload_unchanged_during_rename':True,'external_imports':imports,'dependency':'Existing stable BoPeep private material/texture; not bundled or modified','original_character_paths_overridden':False,'runtime':'NOT SPAWNED; inherited skeleton/physics/postprocess refs require explicit cosmetic-component setup and disabling before activation'}
(a.out/'crook-isolation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
