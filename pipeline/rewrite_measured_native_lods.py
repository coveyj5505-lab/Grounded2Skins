"""Rewrite only measured inline LOD layouts; preserve materials/rest/native tail.

Reuses the tested section/stream encoding and Zen export/bulk relocation.
Input profiles must come from a hash-matched fresh native read-back.
"""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
import numpy as np
from native_buffers import skeleton_signature
from write_resized_lod import array16,section,STREAM_TAIL
p=argparse.ArgumentParser()
for name in ['raw','profiles','buffers','reference','out']:p.add_argument(name,type=Path)
a=p.parse_args();assert not a.out.exists();m=json.loads((a.buffers/'manifest.json').read_text());assert m['skeleton_signature']==skeleton_signature(a.reference);bones=json.loads(a.reference.read_text())['meshes'][0]['bones'];nb=len(bones);assert nb in [192,230]
records=[]
for n in ['indices.bin','positions.bin','static-vertices.bin','skin-weights.bin','colors.bin']:
 b=(a.buffers/n).read_bytes();assert hashlib.sha256(b).hexdigest()==m['files'][n]['sha256'];records.append(b)
active={i for s in m['sections'] for i in s['palette']}
for i in list(active):
 while i>=0:active.add(i);i=bones[i]['parent']
stream=b'\x05\x00'+b''.join(records)+STREAM_TAIL;lod=b'\x05\x00'+struct.pack('<ii',0,1)+array16(range(nb))+struct.pack('<i',len(m['sections']))+b''.join(section(s) for s in m['sections'])+array16(sorted(active))+struct.pack('<I',len(stream))+stream
shutil.copytree(a.raw,a.out);reports=[];pos=np.load(a.buffers/'expected.npz')['positions'];lo,hi=pos.min(0),pos.max(0);center=(lo+hi)/2;extent=(hi-lo)/2
for p in json.loads(a.profiles.read_text()):
 cid=p['chunk'];raw=(a.raw/'chunks'/cid).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['source_sha256'];assert p['skeleton_bones']==nb and p['lod_count'] in [1,4];start,end=p['lod_start'],p['all_lods_end'];assert raw[end-54:end]==STREAM_TAIL and len(raw)-end==100
 s=struct.unpack_from('<15I',raw);entries=[];bulks=[]
 for at in range(s[8],s[9],72):
  off,size=struct.unpack_from('<QQ',raw,at)
  if s[1]+off<=start and s[1]+off+size==len(raw)-4:entries.append((at,size))
 for at in range(60,s[6]-31):
  off,dup,size,flags,cooked=struct.unpack_from('<qqqIB',raw,at)
  if off>0 and dup==-1 and size==flags==cooked==0 and raw[at+29:at+32]==bytes(3):bulks.append(at)
 assert len(entries)==len(bulks)==1
 newlod=lod*p['lod_count'];delta=len(newlod)-(end-start);b=bytearray(raw[:start]+newlod+raw[end:]);struct.pack_into('<Q',b,entries[0][0]+8,entries[0][1]+delta);struct.pack_into('<q',b,bulks[0],start+len(newlod)+4-s[1]);b[p['material_start']-56:p['material_start']]=struct.pack('<7d',*center,*extent,float(np.linalg.norm(extent)))
 assert b[p['material_start']:start]==raw[p['material_start']:start] and b[start+len(newlod):]==raw[end:]
 (a.out/'chunks'/cid).write_bytes(b);reports.append({'chunk':cid,'sha256':hashlib.sha256(b).hexdigest(),'source_sha256':p['source_sha256'],'lods':p['lod_count'],'delta':delta})
(a.out/'native-rewrite-report.json').write_text(json.dumps(reports,indent=2)+'\n');print('REWROTE',len(reports),'native meshes')
