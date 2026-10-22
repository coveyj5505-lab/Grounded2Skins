"""Clone the CURRENT native attack table into a private normal-jab-only package.
Never override CreatureAttacks/ItemAttacks or affect ordinary equipped spears.
Native reader-provided serialized field positions, not runtime offsets, are used.
"""
import argparse,json,struct,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compare_stock_max import names
from assemble_jessie_zen import batch,H
p=argparse.ArgumentParser();p.add_argument('collection',type=Path);p.add_argument('decoded',type=Path);p.add_argument('baseline',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);(a.output/'chunks').mkdir()
cid='9599c95c7cbef52800000001';raw=(a.collection/'chunks'/cid).read_bytes();b=bytearray(raw);summary=struct.unpack_from('<15I',b)
old='/Game/Blueprints/Attacks/ItemAttacks';new='/Game/Blueprints/Attacks/BoPkAttacks';newcid=H(new).to_bytes(8,'little').hex()+'00000001'
layout=json.load(open(a.decoded/'ItemAttacks-row-layout.json'));native=json.load(open(a.decoded/'ItemAttacks.json'))['Rows'];patches=[]
for row in ['Spear','Spear2','Spear3']:
 fields=layout[row]
 for key,expected,value in [('DamageData',20.,8.),('ChargedDamageData',48.,0.),('PerfectChargedDamageData',54.,0.),('ChargeTime',1.5,0.)]:
  field=next(x for x in fields if x['Name']==key)
  if key!='ChargeTime':field=next(x for x in field['Value'] if x['Name']=='Damage')
  at=field['Position'];assert field['Size']==4 and struct.unpack_from('<f',raw,at)[0]==expected
  assert (native[row][key]['Damage'] if key!='ChargeTime' else native[row][key])==expected
  struct.pack_into('<f',b,at,value);patches.append(dict(row=row,field=key,serialized_position=at,old=expected,new=value))
ns,end=names(b,60);assert old in ns and 'ItemAttacks' in ns
updated=[new if n==old else 'BoPkAttacks' if n=='ItemAttacks' else n for n in ns]
encoded=batch(updated);assert len(encoded)==end-60;b[60:end]=encoded
# Fix the one renamed public export; all imported package hashes remain original.
exports=range(summary[8],summary[9],72);changed=0
for at in exports:
 if struct.unpack_from('<Q',b,at+56)[0]==H('ItemAttacks'):
  struct.pack_into('<Q',b,at+56,H('BoPkAttacks'));changed+=1
assert changed==1
(a.output/'chunks'/newcid).write_bytes(b)
imports,_=names(raw,summary[12]);entries=[H(n) for n in imports];store=bytearray(16)
if entries:struct.pack_into('<II',store,0,len(entries),16);store.extend(struct.pack('<'+'Q'*len(entries),*entries))
h=next((a.baseline/'chunks').glob('*00000006'));data=bytearray(h.read_bytes()[:16]+struct.pack('<IQI',1,H(new),len(store))+store+bytes(20));data.extend(struct.pack('<qqI',len(data)+16,4,0));(a.output/'chunks'/h.name).write_bytes(data)
m=json.load(open(a.baseline/'manifest.json'));m['chunk_paths']={newcid:'../../../Augusta/Content/Blueprints/Attacks/BoPkAttacks.uasset'};(a.output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
report={'source_sha256':hashlib.sha256(raw).hexdigest(),'private_package':new,'chunk':newcid,'patches':patches,'range_retained':275,'normal_damage':8,'charge_time':0,'charged_damage':0,'perfect_charged_damage':0,'renamed_public_exports':changed,'native_tables_overridden':False,'runtime_item_binding':'NOT IMPLEMENTED; do not present this preparation as a completed gameplay mod','source_files_modified':False}
(a.output/'preparation-report.json').write_text(json.dumps(report,indent=2)+'\n');print(newcid,'private table prepared')
