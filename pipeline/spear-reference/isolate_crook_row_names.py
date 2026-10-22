"""Give private item/attack rows distinct FNames; preserve native Spear names."""
from pathlib import Path
import sys,json,struct,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compare_stock_max import names
from assemble_jessie_zen import batch
src,layoutdir,out=map(Path,sys.argv[1:]);shutil.copytree(src,out)
itemid='cf393ee92ca15f8900000001';attackid='bce6efd542f97bbd00000001'
item='RivetBoPeepCrook';rows=['RivetCrookJab1','RivetCrookJab2','RivetCrookJab3']
def replace_map(b,ns,end):
 s=list(struct.unpack_from('<15I',b));enc=batch(ns);delta=len(enc)-(end-60);b[60:end]=enc
 for i in (1,5,6,7,8,9,10,11,12,13,14):
  if s[i]>=end:s[i]+=delta
 struct.pack_into('<15I',b,0,*s);return b
b=bytearray((out/'chunks'/itemid).read_bytes());s=struct.unpack_from('<15I',b);ns,end=names(b,60);assert ns[struct.unpack_from('<I',b,s[1]+14)[0]]=='Spear'
newindices={name:len(ns)+i for i,name in enumerate([item]+rows)};ns.extend([item]+rows);struct.pack_into('<I',b,s[1]+14,newindices[item])
layout=json.load(open(layoutdir/'BoPkItemTbl-row-layout.json'))['Spear']
for combo in ['AttackComboData','SwimmingAttackComboData']:
 f=next(v for v in layout if v['Name']==combo);a=next(v for v in f['Value'] if v['Name']=='Attacks');pos=a['Position'];assert struct.unpack_from('<I',b,pos)[0]==3 and a['Size']==46
 for i,new in enumerate(rows):
  at=pos+4+i*14;assert b[at:at+2]==bytes.fromhex('0005');idx,num=struct.unpack_from('<II',b,at+6);assert ns[idx]==['Spear','Spear2','Spear3'][i] and num==0
  struct.pack_into('<I',b,at+6,newindices[new])
(out/'chunks'/itemid).write_bytes(replace_map(b,ns,end))
b=bytearray((out/'chunks'/attackid).read_bytes());ns,end=names(b,60);mapping=dict(zip(['Spear','Spear2','Spear3'],rows));ns=[mapping.get(n,n) for n in ns];(out/'chunks'/attackid).write_bytes(replace_map(b,ns,end))
(out/'unique-row-names.json').write_text(json.dumps({'private_item_row':item,'private_attack_rows':rows,'reason':'Windows private item returned an ordinary spear attack handle despite private cooked references; isolate row names instead of bypassing checks','cause_cache_collision':'suspected, not proven','native_tables_overridden':False},indent=2)+'\n')
print(item,rows)
