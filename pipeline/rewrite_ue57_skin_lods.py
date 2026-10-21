"""Replace validated inline body LODs inside current-build native envelopes.
Preserve every material/skeleton byte, current 112-byte tail and unrelated chunk.
"""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
import numpy as np
from native_buffers import skeleton_signature
from write_resized_lod import array16,section,STREAM_TAIL
p=argparse.ArgumentParser()
for name in ['raw','profiles','buffers','reference','out']:p.add_argument(name,type=Path)
a=p.parse_args();assert not a.out.exists();m=json.loads((a.buffers/'manifest.json').read_text());assert m['skeleton_signature']==skeleton_signature(a.reference);bones=json.loads(a.reference.read_text())['meshes'][0]['bones'];nb=len(bones);assert nb in [188,189,192,230]
records=[]
for n in ['indices.bin','positions.bin','static-vertices.bin','skin-weights.bin','colors.bin']:
 b=(a.buffers/n).read_bytes();assert hashlib.sha256(b).hexdigest()==m['files'][n]['sha256'];records.append(b)
active={i for s in m['sections'] for i in s['palette']}
for i in list(active):
 while i>=0:active.add(i);i=bones[i]['parent']
stream=b'\x05\x00'+b''.join(records)+STREAM_TAIL;lod=b'\x05\x00'+struct.pack('<ii',0,1)+array16(range(nb))+struct.pack('<i',len(m['sections']))+b''.join(section(s) for s in m['sections'])+array16(sorted(active))+struct.pack('<I',len(stream))+stream
shutil.copytree(a.raw,a.out);reports=[];pos=np.load(a.buffers/'expected.npz')['positions'];assert np.isfinite(pos).all();lo,hi=pos.min(0),pos.max(0);center=(lo+hi)/2;extent=(hi-lo)/2
for profile in json.loads(a.profiles.read_text()):
 cid=profile['chunk'];raw=(a.raw/'chunks'/cid).read_bytes();assert hashlib.sha256(raw).hexdigest()==profile['source_sha256'];assert profile['skeleton_bones']==nb and profile['lod_count']==4;start,end=profile['lod_start'],profile['all_lods_end'];assert raw[end-54:end]==STREAM_TAIL and len(raw)-end==112
 s=struct.unpack_from('<15I',raw);entries=[];bulks=[]
 for at in range(s[8],s[9],72):
  off,size=struct.unpack_from('<QQ',raw,at)
  if s[1]+off<=start and s[1]+off+size==len(raw):entries.append((at,size))
 for at in range(60,s[6]-31):
  off,dup,size,flags,cooked=struct.unpack_from('<qqqIB',raw,at)
  if off>0 and dup==-1 and size==flags==cooked==0 and raw[at+29:at+32]==bytes(3):bulks.append(at)
 assert len(entries)==len(bulks)==1
 block=lod*4;delta=len(block)-(end-start);b=bytearray(raw[:start]+block+raw[end:]);struct.pack_into('<Q',b,entries[0][0]+8,entries[0][1]+delta);struct.pack_into('<q',b,bulks[0],struct.unpack_from('<q',raw,bulks[0])[0]+delta);b[profile['material_start']-56:profile['material_start']]=struct.pack('<7d',*center,*extent,float(np.linalg.norm(extent)))
 assert b[profile['material_start']:start]==raw[profile['material_start']:start] and b[start+len(block):]==raw[end:]
 (a.out/'chunks'/cid).write_bytes(b);reports.append({'chunk':cid,'source_sha256':profile['source_sha256'],'sha256':hashlib.sha256(b).hexdigest(),'four_lods':True,'current_native_tail_bytes':112,'materials_and_reference_bytes_exact':True})
(a.out/'skin-fix-rewrite.json').write_text(json.dumps(reports,indent=2)+'\n');print('CURRENT_BUILD_LODS_REWRITTEN',len(reports))
