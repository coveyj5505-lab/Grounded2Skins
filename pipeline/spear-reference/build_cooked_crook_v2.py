"""Clone current native tools table into an isolated cooked crook item table."""
import json,struct,sys,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compare_stock_max import names
from assemble_jessie_zen import batch,H
source,decoded,attacks,out=map(Path,sys.argv[1:])
shutil.copytree(attacks,out)
raw=(source/'chunks/92642d7b60c41f4d00000001').read_bytes();b=bytearray(raw);s=list(struct.unpack_from('<15I',b))
layout=json.load(open(decoded/'Table_Items_Tools-row-layout.json'))['Spear']
throw=next(f for f in layout if f['Name']=='ThrowData')
for f in throw['Value']:
 if f['Name'] in ('bCanThrow','bCanThrowUnderWater'):
  assert f['Size']==1 and b[f['Position']]==1
  b[f['Position']]=0
old='/Game/Blueprints/Items/ItemTables/Table_Items_Tools';new='/Game/Blueprints/Attacks/BoPkItemTbl'
# Redirect this private table's attack import. Native packages remain untouched.
imports,imp_end=names(b,s[12]);idx=imports.index('/Game/Blueprints/Attacks/ItemAttacks')
publics=list(struct.unpack_from('<'+'Q'*((s[7]-s[6])//8),b,s[6]))
changed=0
for at in range(s[7],s[8],8):
 value=struct.unpack_from('<Q',b,at)[0]
 if value>>62==2 and ((value & ((1<<62)-1))>>32)==idx:
  slot=value & 0xffffffff
  if publics[slot]==H('ItemAttacks'):
   struct.pack_into('<Q',b,s[6]+slot*8,H('BoPkAttacks'));changed+=1
assert changed>=1
# Rename both serialized name batches; relocate every following header boundary.
ns,end=names(b,60)
repls={old:new,'Table_Items_Tools':'BoPkItemTbl','/Game/Blueprints/Attacks/ItemAttacks':'/Game/Blueprints/Attacks/BoPkAttacks'}
for at in range(s[8],s[9],72):
 if struct.unpack_from('<Q',b,at+56)[0]==H('Table_Items_Tools'):struct.pack_into('<Q',b,at+56,H('BoPkItemTbl'))
for start,finish,values in sorted([(60,end,ns),(s[12],imp_end,imports)],reverse=True):
 enc=batch([repls.get(n,n) for n in values]);delta=len(enc)-(finish-start);b[start:finish]=enc
 for i in (1,5,6,7,8,9,10,11,12,13,14):
  if s[i]>=finish:s[i]+=delta
struct.pack_into('<15I',b,0,*s)
cid=H(new).to_bytes(8,'little').hex()+'00000001';(out/'chunks'/cid).write_bytes(b)
m=json.load(open(out/'manifest.json'));m['chunk_paths'][cid]='../../../Augusta/Content/Blueprints/Attacks/BoPkItemTbl.uasset';(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
entries={}
for c,p in m['chunk_paths'].items():
 if p.endswith('.uasset'):
  data=(out/'chunks'/c).read_bytes();im,_=names(data,struct.unpack_from('<15I',data)[12]);entries[int.from_bytes(bytes.fromhex(c[:16]),'little')]=[H(v) for v in im]
entries=dict(sorted(entries.items()));buf=bytearray(16*len(entries))
for i,im in enumerate(entries.values()):
 if im:struct.pack_into('<II',buf,i*16,len(im),len(buf)-i*16);buf.extend(struct.pack('<'+'Q'*len(im),*im))
h=next((out/'chunks').glob('*00000006'));header=bytearray(h.read_bytes()[:16]+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(buf))+buf+bytes(20));header.extend(struct.pack('<qqI',len(header)+16,4,0));h.write_bytes(header)
(out/'cooked-v2-evidence.json').write_text(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),'source_package':old,'private_package':new,'redirected_attack_imports':changed,'throw_disabled':True,'runtime_struct_copy':False,'native_packages_overridden':False,'windows_tested':False},indent=2)+'\n')
print(cid,len(b))
