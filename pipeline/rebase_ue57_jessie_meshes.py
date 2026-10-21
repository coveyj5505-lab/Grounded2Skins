"""Rebase accepted Jessie buffers onto fresh UE5.7.4 native object templates.
Does not package/install: private texture templates must also be current-build.
"""
import json,hashlib,struct,sys,subprocess,os
from pathlib import Path
import numpy as np
from compare_stock_max import names
from extract_reference_skeleton import extract
from write_resized_lod import STREAM_TAIL
from assemble_jessie_zen import batch,PRIVATE,H
r=Path('/workspace/mod-work');stage=r/'ue57-migration';old=r/'first-person-stage/jessie-v1';out=stage/'jessie-rebase-v4';out.mkdir(exist_ok=False);(out/'chunks').mkdir();newmeta=json.loads((stage/'Hoops/metadata.json').read_text());newrefs=json.loads((stage/'Hoops/skeletons.json').read_text())['meshes'];oldpaths=json.loads((old/'raw/manifest.json').read_text())['chunk_paths'];reports=[];paths={};env=dict(os.environ,DOTNET_ROOT='/workspace/toolchains/dotnet',DOTNET_CLI_HOME='/workspace/toolchains/dotnet-home',DOTNET_GCHeapHardLimit='0x40000000')
for cid,path in oldpaths.items():
 if '/_Augusta/' not in path or not path.endswith('.uasset'):continue
 entry=next(m for m in newmeta if m['chunk_id']==cid);raw=(stage/'Hoops/chunks'/cid).read_bytes();previous=(old/'raw/chunks'/cid).read_bytes();ns,_=names(previous,60);oldref=extract(previous,ns);newref=next(q for q in newrefs if q['chunk_sha256']==entry['sha256']);assert [(b['name'],b['parent']) for b in oldref['bones']]==[(b['name'],b['parent']) for b in newref['bones']]
 def profile(data,meta,refs,label,new=False):
  folder=out/(label+'-'+cid);inputdir=out/(label+'-input');inputdir.mkdir(exist_ok=True);inputfile=inputdir/cid;inputfile.write_bytes(data);mp=inputdir/(cid+'-metadata.json');rp=inputdir/(cid+'-refs.json');m=dict(meta,sha256=hashlib.sha256(data).hexdigest());ref=dict(refs,chunk_sha256=m['sha256']);mp.write_text(json.dumps([m]));rp.write_text(json.dumps({'meshes':[ref]}));cmd=['/workspace/toolchains/dotnet/dotnet',str(Path(__file__).resolve().parent/'native-lod-probe/bin/Release/net10.0/NativeLodProbe.dll'),str(inputfile),str(rp),str(mp),str(folder)]
  if '/Hair/' in path:cmd+=['--no-colors']
  if new:cmd+=['--ue57']
  with (out/(label+'-'+cid+'.log')).open('w') as log:subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  return json.loads((folder/'mesh.json').read_text())
 s0=struct.unpack_from('<15I',previous);oldmeta=dict(entry,name_map=ns);pold=profile(previous,oldmeta,oldref,'old');pnew=profile(raw,entry,newref,'new',True);s=list(struct.unpack_from('<15I',raw));start,end=pnew['lod_start'],pnew['all_lods_end'];block=previous[pold['lod_start']:pold['all_lods_end']];assert pold['lod_count']==pnew['lod_count']==4;assert all(previous[q['end']-54:q['end']]==STREAM_TAIL for q in pold['lods']);assert len(raw)-end==112
 b=bytearray(raw[:start]+block+raw[end:]);delta=len(block)-(end-start);entries=[]
 for at in range(s[8],s[9],72):
  off,size=struct.unpack_from('<QQ',raw,at)
  if s[1]+off<=start and s[1]+off+size==len(raw):entries.append((at,size))
 assert len(entries)==1;struct.pack_into('<Q',b,entries[0][0]+8,entries[0][1]+delta);bulks=[]
 for at in range(60,s[6]-31):
  off,dup,size,flags,cooked=struct.unpack_from('<qqqIB',raw,at)
  if off>0 and dup==-1 and size==flags==cooked==0 and raw[at+29:at+32]==bytes(3):bulks.append(at)
 assert len(bulks)==1;oldoffset=struct.unpack_from('<q',raw,bulks[0])[0];assert 0<oldoffset<len(raw);struct.pack_into('<q',b,bulks[0],oldoffset+delta);assert b[start+len(block):]==raw[end:]
 if '/Hair/' not in path:
  # Preserve exact accepted FP triangle/section split: head0, body5.
  assert set(np.fromfile(out/('old-'+cid)/'triangle-materials.u16',dtype='<u2'))=={0,5};assert [pold['materials'][i]['name'] for i in [0,5]]==[pnew['materials'][i]['name'] for i in [0,5]]
  material=pnew['materials'][0]['package_index'];assert material<0
  for slot in [0,5]:struct.pack_into('<i',b,pnew['materials'][slot]['record_start'],material)
  P=np.fromfile(out/('old-'+cid)/'positions.f32',dtype='<f4').reshape(-1,3);lo,hi=P.min(0),P.max(0);center=(lo+hi)/2;extent=(hi-lo)/2;b[pnew['material_start']-56:pnew['material_start']]=struct.pack('<7d',*center,*extent,float(np.linalg.norm(extent)))
  obj=struct.unpack_from('<Q',b,s[7]+(-material-1)*8)[0];assert obj>>62==2;pkgidx=(obj&((1<<62)-1))>>32;hashidx=obj&0xffffffff;imp,tail=names(raw,s[12]);numbers=raw[tail:s[1]];assert len(numbers)==4*len(imp);original=imp[pkgidx];assert original.endswith('/MI_Character_fem02_Ally_Head');assert struct.unpack_from('<Q',b,s[6]+hashidx*8)[0]==H(original.rsplit('/',1)[-1]);struct.pack_into('<Q',b,s[6]+hashidx*8,H(PRIVATE.rsplit('/',1)[-1]));imp[pkgidx]=PRIVATE;nb=batch(imp)+numbers;ndelta=len(nb)-(s[1]-s[12]);b=bytearray(bytes(b[:s[12]])+nb+bytes(b[s[1]:]));s[1]+=ndelta;s[5]+=ndelta;struct.pack_into('<15I',b,0,*s)
 (out/'chunks'/cid).write_bytes(b);paths[cid]=path;newnames,_=names(b,60);actualmeta=dict(entry,name_map=newnames);actualref=extract(bytes(b),newnames);assert json.loads(json.dumps(actualref['bones']))==newref['bones'];pactual=profile(bytes(b),actualmeta,actualref,'rebased',True)
 for f in ['positions.f32','indices.u32','uv0.f32','weights.u16','joints.u16','normals.f32','tangents.f32','triangle-materials.u16']:
  if (out/('old-'+cid)/f).exists():assert (out/('old-'+cid)/f).read_bytes()==(out/('rebased-'+cid)/f).read_bytes(),f
 reports.append({'chunk':cid,'path':path,'old_bones':oldref['bone_count'],'new_bones':newref['bone_count'],'same_names_parents':True,'frozen_shape_weights_UVs_FP_sections_byte_exact':True,'new_object_prefix_and_post_LOD_data_used':True,'new_native_tail_bytes':112,'old_Lod_buffer_bytes_reused':len(block),'new_sha256':hashlib.sha256(b).hexdigest()});print('REBASED',path,flush=True)
(out/'mesh-paths.json').write_text(json.dumps(paths,indent=2)+'\n');(out/'mesh-validation.json').write_text(json.dumps({'status':'PASS_NATIVE_REBASE_PRIVATE_TEXTURES_PENDING','meshes':reports,'gameplay':'NOT TESTED','geometry_rig_refitting':False,'new_UObject_prefix_native_tail_and_reference_skeletons_from_original_57_templates':True},indent=2)+'\n')
