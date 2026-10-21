"""Fresh5.7.4 object templates for frozen root-rigid cosmetic accessories."""
import argparse,json,struct,hashlib,subprocess,os
from pathlib import Path
import numpy as np
from compare_stock_max import names
from extract_reference_skeleton import extract
from write_resized_lod import STREAM_TAIL
from assemble_jessie_zen import batch,H
from ue57_accessory_config import CONFIG,R
p=argparse.ArgumentParser();p.add_argument('accessory',choices=CONFIG);p.add_argument('out',type=Path);a=p.parse_args();c=CONFIG[a.accessory];out=a.out;out.mkdir(exist_ok=False);(out/'chunks').mkdir();stage=R/'ue57-migration';oldpaths=json.loads((c['old']/'manifest.json').read_text())['chunk_paths'];stock=stage/'Willow';template_entry=next(m for m in json.loads((stock/'metadata.json').read_text()) if m['path'].endswith('/SK_Female_Teen_01.uasset'));template=(stock/'chunks'/template_entry['chunk_id']).read_bytes();nn,_=names(template,60);nr=extract(template,nn);pn=json.loads((stock/'body-ue57/mesh.json').read_text());source_pkg='/Game/'+template_entry['path'].split('/Content/',1)[1][:-7];private=f'/Game/{c["namespace"]}/Art/Characters/Player_Male01/Textures/MI_Character_Male01_{c["tag"]}_Apparel01';env=dict(os.environ,DOTNET_ROOT='/workspace/toolchains/dotnet',DOTNET_GCHeapHardLimit='0x40000000');paths={};records=[]
def profile(data,names_,ref,cid,path,label,new):
 folder=out/(label+'-'+cid);inp=out/(label+'-input');inp.mkdir(exist_ok=True);(inp/cid).write_bytes(data);sha=hashlib.sha256(data).hexdigest();mp=inp/(cid+'.meta.json');rp=inp/(cid+'.refs.json');mp.write_text(json.dumps([dict(path=path,chunk_id=cid,name_map=names_,sha256=sha)]));rp.write_text(json.dumps({'meshes':[dict(ref,chunk_sha256=sha)]}));cmd=['/workspace/toolchains/dotnet/dotnet',str(Path(__file__).parent/'native-lod-probe/bin/Release/net10.0/NativeLodProbe.dll'),str(inp/cid),str(rp),str(mp),str(folder)]+(['--ue57'] if new else [])
 with (out/(label+'-'+cid+'.log')).open('w') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 return json.loads((folder/'mesh.json').read_text()),folder
for cid,path in oldpaths.items():
 if not path.endswith('.uasset') or '/Textures/' in path:continue
 previous=(c['old']/'chunks'/cid).read_bytes();on,_=names(previous,60);oref=extract(previous,on);po,od=profile(previous,on,oref,cid,path,'old',False);assert po['used_bones']==[0] and po['lod_count']==4 and oref['bone_count']==nr['bone_count']==192;assert [(b['name'],b['parent']) for b in oref['bones']]==[(b['name'],b['parent']) for b in nr['bones']];block=previous[po['lod_start']:po['all_lods_end']];assert all(previous[l['end']-54:l['end']]==STREAM_TAIL for l in po['lods']);assert set(np.fromfile(od/'triangle-materials.u16',dtype='<u2'))=={0};start,end=pn['lod_start'],pn['all_lods_end'];s=list(struct.unpack_from('<15I',template));b=bytearray(template[:start]+block+template[end:]);delta=len(block)-(end-start);exports=[]
 for at in range(s[8],s[9],72):
  off,size=struct.unpack_from('<QQ',template,at)
  if s[1]+off<=start and s[1]+off+size==len(template):exports.append((at,size))
 assert len(exports)==1;struct.pack_into('<Q',b,exports[0][0]+8,exports[0][1]+delta);bulks=[]
 for at in range(60,s[6]-31):
  off,dup,size,flags,cooked=struct.unpack_from('<qqqIB',template,at)
  if off>0 and dup==-1 and size==flags==cooked==0 and template[at+29:at+32]==bytes(3):bulks.append(at)
 assert len(bulks)==1;struct.pack_into('<q',b,bulks[0],struct.unpack_from('<q',template,bulks[0])[0]+delta);assert b[start+len(block):]==template[end:]
 P=np.fromfile(od/'positions.f32',dtype='<f4').reshape(-1,3);lo,hi=P.min(0),P.max(0);center=(lo+hi)/2;extent=(hi-lo)/2;b[pn['material_start']-56:pn['material_start']]=struct.pack('<7d',*center,*extent,float(np.linalg.norm(extent)))
 pkg='/Game/'+path.split('/Content/',1)[1][:-7];local,endnames=names(b,60);nb=batch([pkg if n==source_pkg else n for n in local]);assert len(nb)==endnames-60;b[60:endnames]=nb;material=pn['materials'][0]['package_index'];assert material<0;obj=struct.unpack_from('<Q',b,s[7]+(-material-1)*8)[0];assert obj>>62==2;pi=(obj&((1<<62)-1))>>32;hi=obj&0xffffffff;imp,tail=names(template,s[12]);numbers=template[tail:s[1]];assert len(numbers)==4*len(imp);assert struct.unpack_from('<Q',b,s[6]+hi*8)[0]==H(imp[pi].rsplit('/',1)[-1]);struct.pack_into('<Q',b,s[6]+hi*8,H(private.rsplit('/',1)[-1]));imp[pi]=private;nb=batch(imp)+numbers;ndelta=len(nb)-(s[1]-s[12]);b=bytearray(bytes(b[:s[12]])+nb+bytes(b[s[1]:]));s[1]+=ndelta;s[5]+=ndelta;struct.pack_into('<15I',b,0,*s);assert H(pkg).to_bytes(8,'little').hex()+'00000001'==cid;(out/'chunks'/cid).write_bytes(b);paths[cid]=path;fn,_=names(b,60);fr=extract(bytes(b),fn);pa,ad=profile(bytes(b),fn,fr,cid,path,'rebased',True)
 for f in od.iterdir():
  if f.suffix in ['.f32','.u16','.u32','.rgba8']:assert f.read_bytes()==(ad/f.name).read_bytes(),f.name
 assert pa['used_bones']==[0] and pa['lod_count']==4;records.append(dict(chunk=cid,path=path,has_colors=True,frozen_static_geometry_streams_exact=True,current_reference_bones=192));print('REBASED',a.accessory,pkg,flush=True)
(out/'mesh-paths.json').write_text(json.dumps(paths,indent=2)+'\n');(out/'mesh-validation.json').write_text(json.dumps({'accessory':a.accessory,'status':'PASS_NATIVE_REBASE','meshes':records,'private_material':private,'runtime':'NOT TESTED ON5.7.4'},indent=2)+'\n')
