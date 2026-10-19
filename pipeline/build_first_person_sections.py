"""Candidate native first-person material-section repair for four skins.
Keep every triangle/attribute, original bone tables, asset paths and textures.
Runtime visibility is a hypothesis until a Windows camera-switch test passes.
"""
import argparse,json,struct,hashlib,shutil,subprocess,os
from pathlib import Path
import numpy as np
from cityhash import CityHash64
from native_buffers import encode,skeleton_signature,require
from compare_stock_max import names
from write_resized_lod import section,array16,STREAM_TAIL

ROOT=Path('/workspace/mod-work');DOTNET='/workspace/toolchains/dotnet/dotnet';PIPE=Path(__file__).resolve().parent
CONFIG={
 'Buzz':dict(stage=ROOT/'buzz-v2-stage',raw='final-unpacked',geometry='atlas/Buzz-atlas-SKINNED.npz',body=['cd809abc483f179000000001','8021448bfc8c514500000001'],head_slot=5,mod_name='zBuzzFP_P',names={0:'Max_Apparel_01',5:'Max_Head'}),
 'Woody':dict(stage=ROOT/'woody-stage/final-check-v1',raw='final-unpacked',geometry='../geometry-v1/Woody-geometry-SKINNED.npz',body=['b0baaf49556b7e2200000001','69965555c28c2aae00000001'],head_slot=3,mod_name='zWoodyFP_P',names={}),
 'Jessie':dict(stage=ROOT/'jessie-v2-stage/final-check-v4',raw='final-unpacked',geometry='../geometry-v4/Jessie-geometry-SKINNED.npz',body=['911395b71b48cf1a00000001','32e8e66fd14d9e8d00000001'],head_slot=0,body_slot=5,mod_name='zJessieFP_P',names={}),
 'BoPeep':dict(stage=ROOT/'bopeep-v2-stage/final-check-v1',raw='final-unpacked',geometry='../geometry-v3/BoPeep-geometry-SKINNED.npz',body=['2ee2517f02d2199900000001','5bf07aadb2b863d000000001'],head_slot=3,mod_name='zBoPeepFP_P',names={})}
def append_names(raw,added):
 old,end=names(raw,60);require(not any(n in old for n in added),'Only genuinely new names');allnames=old+added;require(all(n.isascii() for n in allnames),'ASCII batch only')
 count,size,version=struct.unpack_from('<IIQ',raw,60);oldhash=list(struct.unpack_from('<'+'Q'*count,raw,76));newhash=oldhash+[CityHash64(n.lower()) for n in added];enc=[n.encode() for n in allnames]
 batch=struct.pack('<IIQ',len(allnames),sum(map(len,enc)),version)+struct.pack('<'+'Q'*len(allnames),*newhash)+b''.join(struct.pack('>H',len(n)) for n in enc)+b''.join(enc)
 delta=len(batch)-(end-60);b=bytearray(raw[:60]+batch+raw[end:]);s=list(struct.unpack_from('<15I',b));s[1]+=delta;s[5]+=delta
 # UE5.6 also stores cell import/export map offsets in summary words13/14.
 # They delimit the export map and must move with appended FName entries.
 for k in range(6,15):
  if s[k]:require(s[k]>=end,'Unexpected offset inside name batch');s[k]+=delta
 struct.pack_into('<15I',b,0,*s);require(names(b,60)[0]==allnames,'Name roundtrip failed');return b,delta
def run(command,log):
 env=dict(os.environ,DOTNET_ROOT='/workspace/toolchains/dotnet',DOTNET_CLI_HOME='/workspace/toolchains/dotnet-home')
 with log.open('w') as f:r=subprocess.run(list(map(str,command)),env=env,stdout=f,stderr=subprocess.STDOUT)
 require(r.returncode==0,'Command failed; see '+str(log))
def build(character,out):
 c=CONFIG[character];require(not out.exists(),'New output only');out.mkdir(parents=True);stage=c['stage'];source=stage/c['raw'];meta=stage/'final-metadata.json';refs=json.loads((stage/'final-skeletons.json').read_text())['meshes'];base=[]
 for cid in c['body']:
  dest=out/('baseline-'+cid);run([DOTNET,PIPE/'native-lod-probe/bin/Release/net10.0/NativeLodProbe.dll',source/'chunks'/cid,stage/'final-skeletons.json',meta,dest],out/(cid+'-baseline.log'));p=json.loads((dest/'mesh.json').read_text());p['chunk']=cid;base.append(p)
 main=next(x for x in refs if x['chunk_sha256']==base[0]['source_sha256']);reference=out/'reference.json';reference.write_text(json.dumps({'meshes':[main]},indent=2)+'\n');signature=skeleton_signature(reference)
 data=dict(np.load(stage/c['geometry']));require(str(data['skeleton_signature'])==signature,'Different reference signature')
 # Buzz's saved source OBJ UVs precede atlas packing. Recover the exact
 # already-working UVs by original input vertex ID from the baseline encoder.
 oldbuffers=stage/('native-buffers' if character=='Buzz' else '../buffers-v4' if character=='Jessie' else '../buffers-v1');oldexp=np.load(oldbuffers/'expected.npz');source_ids=oldexp['source_vertices'];uv=data['uv0'].copy();uv[source_ids]=oldexp['uv0'];require(np.array_equal(uv[source_ids],oldexp['uv0']),'Ambiguous baseline UV seams');data['uv0']=uv
 bones=main['bones'];head={b['index'] for b in bones if b['name']=='head_JNT'}
 for b in bones:
  if b['parent'] in head:head.add(b['index'])
 fraction=np.where(np.isin(data['joints'],sorted(head)),data['weights'],0).sum(1);head_tri=np.max(fraction[data['indices']],axis=1)>.25;require(head_tri.any() and (~head_tri).any(),'Head split empty')
 data['materials']=np.where(head_tri,c['head_slot'],c.get('body_slot',0)).astype('u2');data['material_count']=np.asarray(len(base[0]['materials']));np.savez_compressed(out/'geometry.npz',**data);manifest=encode(data,signature,out/'buffers');shutil.copytree(source,out/'raw');reports=[]
 records=[(out/'buffers'/n).read_bytes() for n in ['indices.bin','positions.bin','static-vertices.bin','skin-weights.bin','colors.bin']];sections=manifest['sections'];active={i for s in sections for i in s['palette']}
 for i in list(active):
  while i>=0:active.add(i);i=bones[i]['parent']
 active=sorted(active);nb=len(bones);stream=b'\x05\x00'+b''.join(records)+STREAM_TAIL;lod=b'\x05\x00'+struct.pack('<ii',0,1)+array16(range(nb))+struct.pack('<i',len(sections))+b''.join(section(s) for s in sections)+array16(active)+struct.pack('<I',len(stream))+stream
 for p in base:
  cid=p['chunk'];raw=(source/'chunks'/cid).read_bytes();require(hashlib.sha256(raw).hexdigest()==p['source_sha256'],'Input changed');require(p['skeleton_bones']==nb,'Bone table differs');start,end=p['lod_start'],p['all_lods_end'];require(len(raw)-end==100 and raw[-4:]==bytes.fromhex('c1832a9e'),'Unknown tail');s=struct.unpack_from('<15I',raw);header=s[1];entries=[]
  for at in range(s[8],s[9],72):
   offset,size=struct.unpack_from('<QQ',raw,at)
   if header+offset<=start and header+offset+size==len(raw)-4:entries.append((at,size))
  require(len(entries)==1,'Ambiguous mesh export');bulks=[]
  for at in range(60,s[6]-31):
   old,dup,size0,flags,cooked=struct.unpack_from('<qqqIB',raw,at)
   if old>0 and dup==-1 and size0==flags==cooked==0 and raw[at+29:at+32]==bytes(3):bulks.append(at)
  require(len(bulks)==1,'Ambiguous empty Nanite bulk');newlods=lod*p['lod_count'];delta=len(newlods)-(end-start);b=bytearray(raw[:start]+newlods+raw[end:]);struct.pack_into('<Q',b,entries[0][0]+8,entries[0][1]+delta);struct.pack_into('<q',b,bulks[0],start+len(newlods)+4-header)
  headmat=p['materials'][c['head_slot']];bodymat=p['materials'][0];require(bodymat['package_index']<0,'Private material must be imported');struct.pack_into('<i',b,headmat['record_start'],bodymat['package_index']);struct.pack_into('<i',b,p['materials'][c.get('body_slot',0)]['record_start'],bodymat['package_index'])
  nm,_=names(raw,60);added=[];renamed=[]
  for slot,name in c['names'].items():
   if name not in nm+added:added.append(name)
   index=(nm+added).index(name);at=p['materials'][slot]['record_start']+4;struct.pack_into('<ii',b,at,index,0);renamed.append({'slot':slot,'old':p['materials'][slot]['name'],'new':name})
  require(b[start+len(newlods):]==raw[end:],'Native tail changed');name_delta=0
  if added:b,name_delta=append_names(b,added)
  (out/'raw/chunks'/cid).write_bytes(b);reports.append({'chunk':cid,'old_sha256':p['source_sha256'],'new_sha256':hashlib.sha256(b).hexdigest(),'LOD_count':p['lod_count'],'head_material_slot':c['head_slot'],'body_material_slot':c.get('body_slot',0),'head_material_ref_same_private_atlas_as_body':True,'slot_names_restored':renamed,'name_map_header_delta':name_delta,'LOD_byte_delta':delta,'original_imports_material_shaders_textures_unchanged':True})
 report={'character':character,'mod_name':c['mod_name'],'head_triangles':int(head_tri.sum()),'body_triangles':int((~head_tri).sum()),'head_vertex_weight_threshold':.25,'triangles_deleted':0,'camera_offsets_changed':False,'skeleton_or_animation_changes':False,'native_visibility_behavior':'Hypothesis: original first-person head-material hiding now targets separate head triangles. Must test in Windows.','packages':reports};(out/'section-repair.json').write_text(json.dumps(report,indent=2)+'\n');(out/'baseline-profiles.json').write_text(json.dumps(base,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('character',choices=CONFIG);p.add_argument('new_output',type=Path);a=p.parse_args();build(a.character,a.new_output)
