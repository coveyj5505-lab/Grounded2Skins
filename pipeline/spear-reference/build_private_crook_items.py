"""Build an empty cooked BaseItemData table beside private crook attacks.
Runtime clones the native Spear row with typed CopyScriptStruct, never a global override.
The source single-export UE5.7 DataTable layout is asserted before every write.
"""
import struct,sys,json,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compare_stock_max import names
from assemble_jessie_zen import batch,H
import argparse
p=argparse.ArgumentParser();p.add_argument('private_attack_raw',type=Path);p.add_argument('native_attack_chunk',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.private_attack_raw;out=a.output;shutil.copytree(src,out)
b=bytearray(a.native_attack_chunk.read_bytes());source_sha=hashlib.sha256(b).hexdigest();s=struct.unpack_from('<15I',b);old='/Game/Blueprints/Attacks/ItemAttacks';new='/Game/Blueprints/Attacks/BoPkItemTbl'
assert s[0]==0 and s[1]<len(b) and s[7]<s[8]<s[9]<=s[1]
ns,end=names(b,60);updated=[new if n==old else 'BoPkItemTbl' if n=='ItemAttacks' else n for n in ns];enc=batch(updated);assert len(enc)==end-60;b[60:end]=enc
payload=bytearray(b[s[1]:s[1]+14]);assert payload.hex()=='00030cffffff00000000a9010000';struct.pack_into('<i',payload,10,0)
rowidx=struct.unpack_from('<i',payload,2)[0];impat=s[7]+(-rowidx-1)*8;assert struct.unpack_from('<Q',b,impat)[0]==0x7dd06bf27402cb20;struct.pack_into('<Q',b,impat,0x6efee5c4cdec6595)
at=s[8];assert s[9]-at==72;struct.pack_into('<Q',b,at+8,len(payload));assert struct.unpack_from('<Q',b,at+56)[0]==H('ItemAttacks');struct.pack_into('<Q',b,at+56,H('BoPkItemTbl'))
b=b[:s[1]]+payload;cid=H(new).to_bytes(8,'little').hex()+'00000001';(out/'chunks'/cid).write_bytes(b)
m=json.load(open(out/'manifest.json'));m['chunk_paths'][cid]='../../../Augusta/Content/Blueprints/Attacks/BoPkItemTbl.uasset';(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
entries={}
for c,p in m['chunk_paths'].items():
 if p.endswith('.uasset'):
  n,_=names((out/'chunks'/c).read_bytes(),struct.unpack_from('<15I',(out/'chunks'/c).read_bytes())[12]);entries[int.from_bytes(bytes.fromhex(c[:16]),'little')]=[H(v) for v in n]
entries=dict(sorted(entries.items()));buf=bytearray(16*len(entries))
for i,imp in enumerate(entries.values()):
 if imp:struct.pack_into('<II',buf,i*16,len(imp),len(buf)-i*16);buf.extend(struct.pack('<'+'Q'*len(imp),*imp))
h=next((out/'chunks').glob('*00000006'));header=bytearray(h.read_bytes()[:16]+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(buf))+buf+bytes(20));header.extend(struct.pack('<qqI',len(header)+16,4,0));h.write_bytes(header)
(out/'item-table-preparation.json').write_text(json.dumps({'source_sha256':source_sha,'private_package':new,'chunk':cid,'row_struct':'/Script/Maine.BaseItemData','rows_on_disk':0,'serialized_payload_bytes':len(payload),'source_layout_asserted':True,'native_tables_overridden':False,'row_initialization':'Runtime typed UDataTable.AddRow deep copy; original native Spear row is never edited','windows_execution':'NOT TESTED'},indent=2)+'\n')
print(cid,len(b))
