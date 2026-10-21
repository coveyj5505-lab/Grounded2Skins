"""Build a store for accessory meshes that reuse a separately installed skin MI."""
import argparse,json,struct,shutil
from pathlib import Path
from assemble_jessie_zen import H
from compare_stock_max import names
p=argparse.ArgumentParser();p.add_argument('rebase',type=Path);p.add_argument('source_raw',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.mkdir(exist_ok=False);(a.out/'chunks').mkdir();paths=json.loads((a.rebase/'mesh-paths.json').read_text());entries={}
for cid,path in paths.items():
 b=(a.rebase/'chunks'/cid).read_bytes();(a.out/'chunks'/cid).write_bytes(b);s=struct.unpack_from('<15I',b);imp,end=names(b,s[12]);nums=struct.unpack_from('<'+'i'*len(imp),b,end);entries[int.from_bytes(bytes.fromhex(cid[:16]),'little')]=[H(n if v==0 else n+'_'+str(v-1)) for n,v in zip(imp,nums)]
entries=dict(sorted(entries.items()));buf=bytearray(16*len(entries))
for i,imports in enumerate(entries.values()):
 if imports:struct.pack_into('<II',buf,i*16,len(imports),len(buf)-i*16);buf.extend(struct.pack('<'+'Q'*len(imports),*imports))
header=next((a.source_raw/'chunks').glob('*00000006'));prefix=header.read_bytes()[:16];assert struct.unpack_from('<II',prefix)==(0x496f436e,5);head=bytearray(prefix+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(buf))+buf+bytes(20));head.extend(struct.pack('<qqI',len(head)+16,4,0));(a.out/'chunks'/header.name).write_bytes(head);manifest=json.loads((a.source_raw/'manifest.json').read_text());manifest['chunk_paths']=paths;(a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
