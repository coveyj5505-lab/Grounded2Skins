"""Reuse the Jessie Windows-proven envelope repair for frozen model variants.
Buzz intentionally retains its proven custom230-bone bind table; no model refit.
"""
import argparse,json,hashlib,struct,subprocess,os
from pathlib import Path
import numpy as np
from compare_stock_max import names
from extract_reference_skeleton import extract
from write_resized_lod import STREAM_TAIL,array16
from native_buffers import bulk
from assemble_jessie_zen import batch,H
from build_first_person_sections import append_names
from ue57_skin_config import CONFIG,STAGE
p=argparse.ArgumentParser();p.add_argument('character',choices=CONFIG);p.add_argument('out',type=Path);a=p.parse_args();c=CONFIG[a.character];out=a.out;out.mkdir(exist_ok=False);(out/'chunks').mkdir();stock=STAGE/c['stock'];meta=json.loads((stock/'metadata.json').read_text());oldpaths=json.loads((c['old']/'manifest.json').read_text())['chunk_paths'];results=[];paths={};skipped=[];env=dict(os.environ,DOTNET_ROOT='/workspace/toolchains/dotnet',DOTNET_CLI_HOME='/workspace/toolchains/dotnet-home',DOTNET_GCHeapHardLimit='0x40000000');private=f'/Game/{c["namespace"]}/Art/Characters/Player_Male01/Textures/MI_Character_Male01_{c["tag"]}_Apparel01'
def profile(data,names_,ref,entry,label,hascolors,new):
 cid=entry['chunk_id'];folder=out/(label+'-'+cid);inp=out/(label+'-input');inp.mkdir(exist_ok=True);(inp/cid).write_bytes(data);m=dict(entry,name_map=names_,sha256=hashlib.sha256(data).hexdigest());rr=dict(ref,chunk_sha256=m['sha256']);mp=inp/(cid+'.metadata.json');rp=inp/(cid+'.refs.json');mp.write_text(json.dumps([m]));rp.write_text(json.dumps({'meshes':[rr]}));cmd=['/workspace/toolchains/dotnet/dotnet',str(Path(__file__).parent/'native-lod-probe/bin/Release/net10.0/NativeLodProbe.dll'),str(inp/cid),str(rp),str(mp),str(folder)]+([] if hascolors else ['--no-colors'])+(['--ue57'] if new else [])
 with (out/(label+'-'+cid+'.log')).open('w') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 return json.loads((folder/'mesh.json').read_text()),folder
for cid,path in oldpaths.items():
 if '/_Augusta/' not in path or not path.endswith('.uasset'):continue
 if path.endswith(('PhysicsAsset.uasset','CharSelect.uasset')):skipped.append({'path':path,'reason':'Use current native game asset rather than old override'});continue
 entry=next(v for v in meta if v['chunk_id']==cid);source=(stock/'chunks'/cid).read_bytes();previous=(c['old']/'chunks'/cid).read_bytes();oldnames,_=names(previous,60);oldref=extract(previous,oldnames);newnames,_=names(source,60);newref=extract(source,newnames);body='/Hair/' not in path and 'Peeper' not in path and 'Glasses' not in path;colors=body or a.character=='Buzz'
 oldcolors=colors or (a.character=='Buzz' and not body);po,od=profile(previous,oldnames,oldref,entry,'old',oldcolors,False)
 # Additional bind-bone names are appended without changing existing indices.
 preserve_custom=a.character=='Buzz' and body
 raw=source
 if preserve_custom:
  missing=[n for n in oldnames if n not in newnames and any(b['name']==n for b in oldref['bones'])]
  if missing:raw,_=append_names(raw,missing)
  newnames,_=names(raw,60);newref=extract(raw,newnames)
 pn,nd=profile(raw,newnames,newref,entry,'new',colors,True);s=list(struct.unpack_from('<15I',raw));start,end=pn['lod_start'],pn['all_lods_end'];assert len(raw)-end==112;assert po['lod_count'] in [1,4] and pn['lod_count']==4
 first=po['lods'][0];lod=previous[first['start']:first['end']];assert lod[-54:]==STREAM_TAIL
 if oldcolors and not colors:
  assert not body and po['vertices']==3
  payload=(od/'colors.rgba8').read_bytes();color=b'\x05\x00'+struct.pack('<II',4,po['vertices'])+bulk(4,po['vertices'],payload);at=lod.find(color);assert at>=0 and lod.count(color)==1;streamAt=[];ix=np.fromfile(od/'indices.u32',dtype='<u4')
  for stride,dtype in [(2,'<u2'),(4,'<u4')]:
   key=b'\x05\x00'+bytes([stride])+bulk(stride,len(ix),ix.astype(dtype).tobytes());where=lod.find(key)
   if where>=0:streamAt.append(where)
  assert len(streamAt)==1;where=streamAt[0];oldSize=struct.unpack_from('<I',lod,where-4)[0];assert oldSize==len(lod)-where;lod=bytearray(lod[:at]+lod[at+len(color):]);struct.pack_into('<I',lod,where-4,oldSize-len(color));lod=bytes(lod)
 replacement_ref=raw[newref['offset']:newref['end']]
 if preserve_custom:
  # Reindex only serialized FNames in the original native reference structure.
  # Keep all original parents, rest transforms, bind matrices and LOD indices.
  ref=bytearray(previous[oldref['offset']:oldref['end']]);n=oldref['bone_count'];lookup={name:i for i,name in enumerate(newnames)}
  for at in [4+i*12 for i in range(n)]+[4+n*12+4+n*80+4+i*12 for i in range(n)]:
   ni=struct.unpack_from('<I',ref,at)[0];struct.pack_into('<I',ref,at,lookup[oldnames[ni]])
  replacement_ref=bytes(ref)
 else:
  oldpairs=[(b['name'],b['parent']) for b in oldref['bones']];newpairs=[(b['name'],b['parent']) for b in newref['bones']]
  if oldpairs!=newpairs:
   assert not body and po['vertices']==3 and po['used_bones']==[0]
   n=oldref['bone_count'];assert po['required_bones']==list(range(n));assert lod[:10]==b'\x05\x00'+struct.pack('<ii',0,1);lod=lod[:10]+array16(range(newref['bone_count']))+lod[14+n*2:]
 block=lod*pn['lod_count'];refdelta=len(replacement_ref)-(newref['end']-newref['offset']);delta=refdelta+len(block)-(end-start);b=bytearray(raw[:newref['offset']]+replacement_ref+raw[newref['end']:start]+block+raw[end:]);entries=[]
 for at in range(s[8],s[9],72):
  off,size=struct.unpack_from('<QQ',raw,at)
  if s[1]+off<=newref['offset'] and s[1]+off+size==len(raw):entries.append((at,size))
 assert len(entries)==1;struct.pack_into('<Q',b,entries[0][0]+8,entries[0][1]+delta);bulks=[]
 for at in range(60,s[6]-31):
  off,dup,size,flags,cooked=struct.unpack_from('<qqqIB',raw,at)
  if off>0 and dup==-1 and size==flags==cooked==0 and raw[at+29:at+32]==bytes(3):bulks.append(at)
 assert len(bulks)==1;oldoff=struct.unpack_from('<q',raw,bulks[0])[0];struct.pack_into('<q',b,bulks[0],oldoff+delta);assert b[start+refdelta+len(block):]==raw[end:]
 if body:
  body_slot,head_slot=c['slots'];slots=np.fromfile(od/'triangle-materials.u16',dtype='<u2');assert set(slots)==set(c['slots']);expected=[po['materials'][i]['name'] for i in c['slots']]
  if a.character=='Buzz':
   for slot,wanted in zip(c['slots'],expected):
    current=pn['materials'][slot]['name']
    if current==wanted:continue
    assert wanted in newnames and current in newnames
    for other in pn['materials']:
     if other['slot']!=slot and other['name']==wanted:struct.pack_into('<ii',b,other['record_start']+4,newnames.index(current),0)
    struct.pack_into('<ii',b,pn['materials'][slot]['record_start']+4,newnames.index(wanted),0)
  else:assert expected==[pn['materials'][i]['name'] for i in c['slots']]
  material=pn['materials'][head_slot]['package_index'];assert material<0
  for slot in c['slots']:struct.pack_into('<i',b,pn['materials'][slot]['record_start'],material)
  P=np.fromfile(od/'positions.f32',dtype='<f4').reshape(-1,3);lo,hi=P.min(0),P.max(0);center=(lo+hi)/2;extent=(hi-lo)/2;b[pn['material_start']-56:pn['material_start']]=struct.pack('<7d',*center,*extent,float(np.linalg.norm(extent)))
  obj=struct.unpack_from('<Q',b,s[7]+(-material-1)*8)[0];assert obj>>62==2;pkgidx=(obj&((1<<62)-1))>>32;hashidx=obj&0xffffffff;imp,tail=names(raw,s[12]);numbers=raw[tail:s[1]];assert len(numbers)==4*len(imp);original=imp[pkgidx];assert struct.unpack_from('<Q',b,s[6]+hashidx*8)[0]==H(original.rsplit('/',1)[-1]);struct.pack_into('<Q',b,s[6]+hashidx*8,H(private.rsplit('/',1)[-1]));imp[pkgidx]=private;nb=batch(imp)+numbers;ndelta=len(nb)-(s[1]-s[12]);b=bytearray(bytes(b[:s[12]])+nb+bytes(b[s[1]:]));s[1]+=ndelta;s[5]+=ndelta;struct.pack_into('<15I',b,0,*s)
 (out/'chunks'/cid).write_bytes(b);paths[cid]=path;finalnames,_=names(b,60);actualref=extract(bytes(b),finalnames);expectedref=oldref if preserve_custom else newref;assert json.loads(json.dumps(actualref['bones']))==json.loads(json.dumps(expectedref['bones']));pa,ad=profile(bytes(b),finalnames,actualref,entry,'rebased',colors,True)
 for f in od.iterdir():
  if f.suffix in ['.f32','.u16','.u32','.rgba8'] and not (oldcolors!=colors and f.name=='colors.rgba8'):assert f.read_bytes()==(ad/f.name).read_bytes(),(cid,f.name)
 results.append({'chunk':cid,'path':path,'has_colors':colors,'old_has_colors':oldcolors,'old_lods':po['lod_count'],'new_lods':pa['lod_count'],'old_bones':oldref['bone_count'],'new_bones':actualref['bone_count'],'preserved_custom_bind_table':preserve_custom,'all_frozen_geometry_weights_UVs_FP_sections_exact':True});print('REBASED',a.character,Path(path).name,flush=True)
(out/'mesh-paths.json').write_text(json.dumps(paths,indent=2)+'\n');(out/'mesh-validation.json').write_text(json.dumps({'character':a.character,'status':'PASS_NATIVE_REBASE','meshes':results,'skipped_native_overrides':skipped,'runtime':'NOT TESTED'},indent=2)+'\n')
