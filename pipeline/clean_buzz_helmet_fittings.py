"""Remove only two arm-weighted helmet fittings; preserve every retained attribute.

Uses the already validated first-person mesh, private atlas and native package.
The arm rig is deliberately unchanged: this isolates the moving-piece correction.
"""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
import numpy as np
from native_buffers import encode,skeleton_signature
from write_resized_lod import array16,section,STREAM_TAIL

p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
base=a.baseline;out=a.output;out.mkdir(exist_ok=False)
z=dict(np.load(base/'geometry.npz'));source=np.load('/workspace/mod-work/buzz-v2-stage/source-geometry.npz');fit=np.load('/workspace/mod-work/rig-stage/skinned-stowed-v2-proportions/expected.npz')
component=fit['component'][source['source_vertices'][z['source_vertices']]]
assert np.array_equal(z['positions'],source['positions'][z['source_vertices']])
drop=np.isin(component,[15,55]);corner=drop[z['indices']];assert np.all(corner.all(1)|(~corner).all(1))
keep_tri=~corner.all(1);keep=np.unique(z['indices'][keep_tri]);remap=np.full(len(drop),-1,dtype='i4');remap[keep]=np.arange(len(keep))
assert int((~keep_tri).sum())==336
for cid,bone in [(15,56),(55,160)]:
 assert np.all(z['joints'][component==cid,0]==bone) and np.all(z['weights'][component==cid,0]==1)
data={}
vertex_keys={'positions','normals','tangents','signs','colors','uv0','joints','weights','source_vertices'}
for k,v in z.items():
 data[k]=v[keep] if k in vertex_keys else remap[v[keep_tri]] if k=='indices' else v[keep_tri] if k in {'materials','source_materials'} else v
np.savez_compressed(out/'geometry.npz',**data);np.savez_compressed(out/'retained-map.npz',vertices=keep,triangles=np.where(keep_tri)[0])
manifest=encode(data,skeleton_signature(base/'reference.json'),out/'buffers');bones=json.loads((base/'reference.json').read_text())['meshes'][0]['bones'];active={i for sec in manifest['sections'] for i in sec['palette']}
for i in list(active):
 while i>=0:active.add(i);i=bones[i]['parent']
records=[(out/'buffers'/n).read_bytes() for n in ['indices.bin','positions.bin','static-vertices.bin','skin-weights.bin','colors.bin']]
stream=b'\x05\x00'+b''.join(records)+STREAM_TAIL
lod=b'\x05\x00'+struct.pack('<ii',0,1)+array16(range(230))+struct.pack('<i',len(manifest['sections']))+b''.join(section(s) for s in manifest['sections'])+array16(sorted(active))+struct.pack('<I',len(stream))+stream
shutil.copytree(base/'package/unpacked',out/'raw');reports=[]
for cid in ['cd809abc483f179000000001','8021448bfc8c514500000001']:
 raw=(base/'package/unpacked/chunks'/cid).read_bytes();profile=json.loads((base/('readback-'+cid)/'mesh.json').read_text());assert hashlib.sha256(raw).hexdigest()==profile['source_sha256'];assert profile['lod_count']==1 and profile['skeleton_bones']==230
 start,end=profile['lod_start'],profile['all_lods_end'];s=struct.unpack_from('<15I',raw);entries=[]
 for at in range(s[8],s[9],72):
  off,size=struct.unpack_from('<QQ',raw,at)
  if s[1]+off<=start and s[1]+off+size==len(raw)-4:entries.append((at,size))
 bulk=[]
 for at in range(60,s[6]-31):
  old,dup,size,flags,cooked=struct.unpack_from('<qqqIB',raw,at)
  if old>0 and dup==-1 and size==flags==cooked==0 and raw[at+29:at+32]==bytes(3):bulk.append(at)
 assert len(entries)==len(bulk)==1 and raw[end-54:end]==STREAM_TAIL and len(raw)-end==100
 delta=len(lod)-(end-start);b=bytearray(raw[:start]+lod+raw[end:]);struct.pack_into('<Q',b,entries[0][0]+8,entries[0][1]+delta);struct.pack_into('<q',b,bulk[0],start+len(lod)+4-s[1])
 # Bounds deliberately retain the conservative working baseline extent.
 assert b[profile['material_start']-56:start]==raw[profile['material_start']-56:start] and b[start+len(lod):]==raw[end:]
 (out/'raw/chunks'/cid).write_bytes(b);reports.append({'chunk':cid,'sha256':hashlib.sha256(b).hexdigest()})
(out/'report.json').write_text(json.dumps({'removed_components':[15,55],'removed_triangles':336,'source_body_vertices_preserved_separately':276,'input_render_vertices_removed':int(drop.sum()),'retained_vertices_attributes_exact':True,'head_body_material_split_unchanged':True,'arm_rig_unchanged':True,'reference_skeleton_materials_dependencies_native_tail_unchanged':True,'packages':reports,'runtime':'NOT TESTED'},indent=2)+'\n')
print('Helmet-fitting cleanup encoded; retained triangles:',len(data['indices']))
