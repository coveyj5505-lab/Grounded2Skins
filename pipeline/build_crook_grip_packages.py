"""Three private crook presentations using the Windows-proven accessory template."""
import argparse,hashlib,json,struct,subprocess,sys
from pathlib import Path
import numpy as np
from native_buffers import encode,skeleton_signature
from compare_stock_max import names
from assemble_bopeep_zen import batch,H
p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('out',type=Path);a=p.parse_args();out=a.out;out.mkdir(exist_ok=False);(out/'raw/chunks').mkdir(parents=True)
template=Path('/workspace/mod-work/crook-stage');raw=template/'package-v1/unpacked';cid='4d2d88a628acba9400000001';profile=json.loads((template/'native-readback-v1/mesh.json').read_text());profile['chunk']=cid;assert hashlib.sha256((raw/'chunks'/cid).read_bytes()).hexdigest()==profile['source_sha256'];reference=template/'reference.json';sig=skeleton_signature(reference);oldpkg='/Game/_BoCrook/Art/Characters/Player_Female01/SK_Female_Teen_01';paths={};reports=[]
tp=dict(np.load(a.stage/'tp-export/BoPeep-geometry-SKINNED.npz'));fp=dict(np.load(a.stage/'fp-export/BoPeep-geometry-SKINNED.npz'));mask=fp['source_vertices']<391;keep_tri=mask[fp['indices']].all(1);assert int(keep_tri.sum())==590;used=np.unique(fp['indices'][keep_tri]);lookup=np.full(len(mask),-1,dtype='i4');lookup[used]=np.arange(len(used));bare={}
for k,v in fp.items():
 bare[k]=lookup[v[keep_tri]] if k=='indices' else v[keep_tri] if k=='materials' else v[used] if np.ndim(v)>0 and len(v)==len(mask) else v
for label,namespace,data in [('TP','_BoCrTP1',tp),('FP','_BoCrFP1',fp),('FN','_BoCrFN1',bare)]:
 work=out/label;work.mkdir();data['material_count']=np.array(len(profile['materials']));data['materials']=np.zeros(len(data['indices']),dtype='u2');assert str(data['skeleton_signature'])==sig and np.all(data['joints']==0) and np.all(data['weights'][:,0]==1);np.savez_compressed(work/'geometry.npz',**data);encode(data,sig,work/'buffers');(work/'profiles.json').write_text(json.dumps([profile],indent=2))
 subprocess.run([sys.executable,str(Path(__file__).parent/'rewrite_measured_native_lods.py'),str(raw),str(work/'profiles.json'),str(work/'buffers'),str(reference),str(work/'rewritten')],check=True)
 b=(work/'rewritten/chunks'/cid).read_bytes();ns,end=names(b,60);newpkg=oldpkg.replace('_BoCrook',namespace);assert ns.count(oldpkg)==1;encoded=batch([newpkg if n==oldpkg else n for n in ns]);assert len(encoded)==end-60;target=b[:60]+encoded+b[end:];assert target[end:]==b[end:]
 newcid=H(newpkg).to_bytes(8,'little').hex()+'00000001';(out/'raw/chunks'/newcid).write_bytes(target);paths[newcid]='../../../Augusta/Content/'+newpkg.removeprefix('/Game/')+'.uasset';reports.append({'kind':label,'asset':newpkg+'.SK_Female_Teen_01','chunk':newcid,'vertices':json.loads((work/'buffers/manifest.json').read_text())['output_vertices'],'triangles':len(data['indices'])})
entries={}
for cid in paths:
 b=(out/'raw/chunks'/cid).read_bytes();s=struct.unpack_from('<15I',b);imports,end=names(b,s[12]);nums=struct.unpack_from('<'+'i'*len(imports),b,end);entries[int.from_bytes(bytes.fromhex(cid[:16]),'little')]=[H(n if v==0 else n+'_'+str(v-1)) for n,v in zip(imports,nums)]
entries=dict(sorted(entries.items()));store=bytearray(16*len(entries))
for i,imports in enumerate(entries.values()):
 if imports:struct.pack_into('<II',store,i*16,len(imports),len(store)-i*16);store.extend(struct.pack('<'+'Q'*len(imports),*imports))
header=next((raw/'chunks').glob('*00000006'));b=bytearray(header.read_bytes()[:16]+struct.pack('<I',len(entries))+struct.pack('<'+'Q'*len(entries),*entries)+struct.pack('<I',len(store))+store+bytes(20));b.extend(struct.pack('<qqI',len(b)+16,4,0));(out/'raw/chunks'/header.name).write_bytes(b);manifest=json.loads((raw/'manifest.json').read_text());manifest['chunk_paths']=paths;(out/'raw/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'report.json').write_text(json.dumps({'meshes':reports,'materials':'Existing stable BoPeep private material and textures; unchanged','runtime':'PENDING'},indent=2));print(json.dumps(reports,indent=2))
