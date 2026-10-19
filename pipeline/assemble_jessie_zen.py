"""Build isolated Jessie mesh/material namespace and v5 package store.
Original skeleton, physics, animation and unused material imports remain external.
"""
import argparse,json,struct,hashlib
from pathlib import Path
from cityhash import CityHash64
from compare_stock_max import names
from native_buffers import require
H=lambda s:CityHash64(s.lower().encode('utf-16-le'))
PRIVATE='/Game/_Jessie0/Art/Characters/Player_Male01/Textures/MI_Character_Male01_Jes_Apparel01'

def batch(strings):
 if not strings:return bytes(4)
 enc=[s.encode('ascii') for s in strings];assert all(len(s)<32768 for s in enc)
 return struct.pack('<IIQ',len(enc),sum(map(len,enc)),0xc1640000)+b''.join(struct.pack('<Q',CityHash64(s.lower())) for s in enc)+b''.join(struct.pack('>H',len(s)) for s in enc)+b''.join(enc)

def assemble(cooked,stock,profiles,templates,out):
 require(not out.exists(),'New output only');(out/'chunks').mkdir(parents=True)
 paths={};records=[];profiles=json.loads(profiles.read_text())
 for p in profiles:
  cid=p['chunk'];raw=(cooked/'chunks'/cid).read_bytes();b=bytearray(raw);s=list(struct.unpack_from('<15I',b));imports,end=names(b,s[12]);numbers=raw[end:s[1]];require(len(numbers)==4*len(imports),'Unexpected imported name footer')
  if '/Hair/' not in p['path']:
   index=struct.unpack_from('<i',b,p['material_start']+4)[0];require(index<0,'Expected imported material')
   impoff=s[7]+(-index-1)*8;obj=struct.unpack_from('<Q',b,impoff)[0];require(obj>>62==2,'Unexpected import kind')
   pkgidx=(obj&((1<<62)-1))>>32;hashidx=obj&0xffffffff;old=imports[pkgidx];require(old=='/Game/_Augusta/Art/Characters/Player_Female02/Textures/MI_Character_fem02_Ally_Head','Not a Hoops material')
   hashat=s[6]+hashidx*8;require(struct.unpack_from('<Q',b,hashat)[0]==H(old.split('/')[-1]),'Public export hash mismatch')
   struct.pack_into('<Q',b,hashat,H(PRIVATE.split('/')[-1]));imports[pkgidx]=PRIVATE
   nb=batch(imports)+numbers;delta=len(nb)-(s[1]-s[12]);header=bytes(b[:s[12]])+nb
   require(len(header)==s[1]+delta,'Bad header sizing');b=bytearray(header+raw[s[1]:]);s[1]+=delta;s[5]+=delta;struct.pack_into('<15I',b,0,*s)
   require(b[s[1]:]==raw[struct.unpack_from('<I',raw,4)[0]:],'Native payload changed during import relocation')
   records.append({'chunk':cid,'old_material':old,'new_material':PRIVATE,'native_material_package_index':index,'imported_package_slot':pkgidx,'public_hash_slot':hashidx,'header_size_delta':delta})
  (out/'chunks'/cid).write_bytes(b);paths[cid]=p['path']
 template_manifest=json.loads((templates/'manifest.json').read_text())
 for cid,path in template_manifest['chunk_paths'].items():
  if '/_Jessie0/' not in path:continue
  require(cid not in paths,'Duplicate chunk');(out/'chunks'/cid).write_bytes((templates/'chunks'/cid).read_bytes());paths[cid]=path
 require(sum(p.endswith('.uasset') for p in paths.values())==11,'Expected 6 meshes and 5 private assets')
 entries={}
 for cid,path in paths.items():
  if not path.endswith('.uasset'):continue
  raw=(out/'chunks'/cid).read_bytes();s=struct.unpack_from('<15I',raw);imp,end=names(raw,s[12]);nums=struct.unpack_from('<'+'i'*len(imp),raw,end);imp=[v if n==0 else v+'_'+str(n-1) for v,n in zip(imp,nums)]
  entries[int.from_bytes(bytes.fromhex(cid[:16]),'little')]=[H(v) for v in imp]
 entries=dict(sorted(entries.items()));buf=bytearray(16*len(entries))
 for i,imp in enumerate(entries.values()):
  if imp:struct.pack_into('<II',buf,i*16,len(imp),len(buf)-i*16);buf.extend(struct.pack('<'+'Q'*len(imp),*imp))
 oldheader=next((templates/'chunks').glob('*00000006'));old=oldheader.read_bytes();head=bytearray(old[:16]+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(buf))+buf+bytes(20));head.extend(struct.pack('<qqI',len(head)+16,4,0));(out/'chunks'/oldheader.name).write_bytes(head)
 manifest=dict(template_manifest,chunk_paths=paths);(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (out/'material-isolation.json').write_text(json.dumps({'mesh_material_relocations':records,'packages':11,'chunks':16,'private_namespace':'/Game/_Jessie0','stock_skeleton_physics_and_animation_overrides':False,'buzz_max_paths_overridden':False},indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ['cooked','stock','profiles','templates','out']:ap.add_argument(n,type=Path)
 a=ap.parse_args();assemble(a.cooked,a.stock,a.profiles,a.templates,a.out)
