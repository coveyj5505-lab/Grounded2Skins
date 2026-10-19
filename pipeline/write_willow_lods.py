"""Hash-guarded stock-Willow four-LOD writer. Original skeleton bytes preserved.
New character LODs have no source Willow morph deltas or cloth; four identical
low-poly LODs preserve the source UObject LODInfo layout. Hair uses invisible
coincident triangles rather than an unverified zero-LOD asset.
"""
import argparse,json,hashlib,struct
from pathlib import Path
import numpy as np
from native_buffers import require,skeleton_signature,bulk,packed_normal
from write_resized_lod import section,array16,STREAM_TAIL

def hair_buffers():
 n=3;tx=packed_normal(np.tile([1.,0,0],(n,1)),np.ones(n));nz=packed_normal(np.tile([0.,0,1],(n,1)),np.ones(n))
 skin=np.zeros((n,16),dtype='u1');skin[:,8]=255
 records=[b'\x04'+bulk(4,3,np.array([0,1,2],dtype='<u4').tobytes()),struct.pack('<II',12,n)+bulk(12,n,bytes(36)),b'\x05\x00'+struct.pack('<iiii',1,n,0,0)+bulk(8,n,np.concatenate((tx,nz),1).tobytes())+bulk(4,n,bytes(12)),b'\x05\x00'+struct.pack('<iIIIII',0,8,n*8,n,0,0)+bulk(1,n*16,skin.tobytes())+b'\x05\x00'+struct.pack('<i',0)+bulk(4,0,b'')]
 sec={'material':0,'index_start':0,'triangles':1,'vertex_start':0,'vertices':3,'palette':[0],'max_influences':1}
 return records,[sec],[0],np.zeros((3,3))

def write(stock,profiles,buffers,reference,out):
 require(not out.exists(),'New output required');out.mkdir();(out/'chunks').mkdir()
 manifest=json.loads((buffers/'manifest.json').read_text());require(manifest['skeleton_signature']==skeleton_signature(reference),'Wrong skeleton')
 bones=json.loads(reference.read_text())['meshes'][0]['bones'];reports=[]
 for p in json.loads(profiles.read_text()):
  raw=(stock/'chunks'/p['chunk']).read_bytes();require(hashlib.sha256(raw).hexdigest()==p['sha256'],'Source hash mismatch')
  hair='/Hair/' in p['path'];nb=16 if hair else 192;require(p['skeleton_bones']==nb and p['lod_count']==4,'Unsupported profile')
  if hair:records,sections,active,pos=hair_buffers()
  else:
   records=[]
   for name in ['indices.bin','positions.bin','static-vertices.bin','skin-weights.bin','colors.bin']:
    b=(buffers/name).read_bytes();require(hashlib.sha256(b).hexdigest()==manifest['files'][name]['sha256'],'Buffer changed');records.append(b)
   sections=manifest['sections'];active=set(x for s in sections for x in s['palette'])
   for i in list(active):
    while i>=0:active.add(i);i=bones[i]['parent']
   active=sorted(active);pos=np.load(buffers/'expected.npz')['positions']
  stream=b'\x05\x00'+b''.join(records)+STREAM_TAIL
  lod=b'\x05\x00'+struct.pack('<ii',0,1)+array16(range(nb))+struct.pack('<i',len(sections))+b''.join(section(s) for s in sections)+array16(active)+struct.pack('<I',len(stream))+stream
  start,end=p['lod_start'],p['all_lods_end'];require(len(raw)-end==100 and raw[-4:]==bytes.fromhex('c1832a9e'),'Unknown native tail')
  require(struct.unpack_from('<i',raw,start-4)[0]==4,'LOD count differs')
  s=struct.unpack_from('<15I',raw);header=s[1];exp=s[8];candidates=[]
  for entry in range(exp,s[9],72):
   offset,size=struct.unpack_from('<QQ',raw,entry)
   if header+offset<=start and header+offset+size==len(raw)-4:candidates.append((entry,offset,size))
  require(len(candidates)==1,'Mesh export extent ambiguous');entry,offset,size=candidates[0]
  # Exact zero-size native bulk-map record. Offset need not be live for size=0.
  bulkc=[]
  for at in range(60,s[6]-31):
   old,dup,size0,flags,cooked=struct.unpack_from('<qqqIB',raw,at)
   if old>0 and dup==-1 and size0==0 and flags==0 and cooked==0 and raw[at+29:at+32]==bytes(3):bulkc.append((at,old))
  require(len(bulkc)==1,'Zero Nanite bulk record ambiguous');bat,old=bulkc[0]
  newlods=lod*4;delta=len(newlods)-(end-start);target=bytearray(raw[:start]+newlods+raw[end:]);struct.pack_into('<Q',target,entry+8,size+delta);struct.pack_into('<q',target,bat,start+len(newlods)+4-header)
  lo,hi=pos.min(0),pos.max(0);origin=(lo+hi)/2;extent=(hi-lo)/2
  target[p['material_start']-56:p['material_start']]=struct.pack('<7d',*origin,*extent,float(np.linalg.norm(extent)))
  require(target[p['material_start']:start]==raw[p['material_start']:start],'Original materials/skeleton/cooked flags changed')
  require(target[start+len(newlods):]==raw[end:],'Native post-LOD tail changed')
  (out/'chunks'/p['chunk']).write_bytes(target)
  reports.append({'chunk':p['chunk'],'path':p['path'],'sha256':hashlib.sha256(target).hexdigest(),'source_sha256':p['sha256'],'delta':delta,'lod_start':start,'lod_size':len(lod),'lod_count':4,'hair_stub':hair,'skeleton_and_material_prefix_unchanged':True,'native_tail_preserved':True,'source_morph_buffers_replaced_with_empty':True})
 (out/'write-report.json').write_text(json.dumps({'packages':reports,'runtime_test':'NOT RUN','original_files_modified':False},indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__)
 for name in ['stock','profiles','buffers','reference','out']:ap.add_argument(name,type=Path)
 a=ap.parse_args();write(a.stock,a.profiles,a.buffers,a.reference,a.out)
